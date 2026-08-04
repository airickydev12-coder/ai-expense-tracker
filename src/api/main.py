"""
Main FastAPI application.

This module creates the API application and registers
routers, middleware, exception handlers, and startup events.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routers import dashboard
from src.api.routers.accounts import router as accounts_router
from src.api.routers.admin import router as admin_router
from src.api.routers.auth import router as auth_router
from src.api.routers.bills import router as bills_router
from src.api.routers.budgets import router as budgets_router
from src.api.routers.coach import router as coach_router
from src.api.routers.debt import router as debt_router
from src.api.routers.expenses import router as expenses_router
from src.api.routers.forecasting import router as forecasting_router
from src.api.routers.goals import router as goals_router
from src.api.routers.health import router as health_router
from src.api.routers.history import router as history_router
from src.api.routers.income import router as income_router
from src.api.routers.notifications import router as notifications_router
from src.api.routers.recommendations import (
    router as recommendations_router,
)
from src.api.routers.recurring_expenses import (
    router as recurring_expenses_router,
)
from src.api.routers.scenarios import router as scenarios_router
from src.core.config import (
    COOKIE_SECURE,
    ENVIRONMENT,
    JWT_SECRET_KEY,
    NOTIFICATION_CHECK_INTERVAL_MINUTES,
)
from src.core.db import initialize_database
from src.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleError,
    ExternalServiceError,
    NotFoundError,
    PersistenceError,
    RateLimitError,
    ValidationError,
)
from src.core.logging import configure_logging, get_logger
from src.financial.notifications.service import check_and_send_notifications
from src.financial.scenarios.factory import register_default_scenario_handlers
from src.financial.users.repository import list_active_users

configure_logging(console_level=logging.INFO)

logger = get_logger(__name__)


_INSECURE_JWT_SECRET = "dev-insecure-secret-change-me"


def _validate_startup_config() -> None:
    """Validate security-sensitive config before the app starts serving requests.

    Fails fast (refuses to start) rather than merely warning when running with
    ENVIRONMENT=production and the placeholder JWT secret still in place -- a
    log warning is easy to miss in a self-hosted deployment, and signing
    tokens with a public, checked-into-git default secret is a real
    compromise, not a cosmetic issue. COOKIE_SECURE is only ever warned about,
    never fatal here: the current LAN deployment is legitimately plain HTTP
    (see COOKIE_SECURE's definition in src/core/config.py), so it's a real,
    supported configuration, not a mistake to block on.
    """
    if ENVIRONMENT == "production" and JWT_SECRET_KEY == _INSECURE_JWT_SECRET:
        raise RuntimeError(
            "Refusing to start: JWT_SECRET_KEY is still the insecure default while "
            "ENVIRONMENT=production. Set a real secret, e.g. "
            'python -c "import secrets; print(secrets.token_urlsafe(64))"'
        )

    if JWT_SECRET_KEY == _INSECURE_JWT_SECRET:
        logger.warning(
            "JWT_SECRET_KEY is using the insecure default — set a real secret "
            "in .env before relying on auth for anything real."
        )

    if not COOKIE_SECURE:
        logger.warning(
            "COOKIE_SECURE is false — the refresh-token cookie will be sent over "
            "plain HTTP. Set COOKIE_SECURE=true once this deployment is served over HTTPS."
        )


def _check_and_send_notifications_for_all_users() -> None:
    """Run the notification check for every active user.

    Each domain's data is now isolated per user and lazily loaded on first
    access (see src/financial/application/financial_state.py) — there's no
    more app-wide "load everything at startup" step, so this scheduled job
    (unlike a request) must resolve the user list itself and iterate it.
    A failure for one user (e.g. a bad email) is logged and skipped rather
    than aborting the rest of the run.
    """
    for user in list_active_users():
        try:
            check_and_send_notifications(user.id, user.email)
        except Exception:
            logger.exception("Notification check failed for user %d", user.id)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize the database and start the notification scheduler on
    startup; stop the scheduler on shutdown."""
    initialize_database()
    register_default_scenario_handlers()
    _validate_startup_config()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _check_and_send_notifications_for_all_users,
        trigger=IntervalTrigger(minutes=NOTIFICATION_CHECK_INTERVAL_MINUTES),
        id="check_and_send_notifications",
    )
    scheduler.start()
    logger.info(
        "Notification scheduler started (every %d minute(s))",
        NOTIFICATION_CHECK_INTERVAL_MINUTES,
    )

    try:
        yield
    finally:
        scheduler.shutdown()


app = FastAPI(
    title="AI Expense Tracker API",
    description="REST API for the AI Expense Tracker financial platform.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # allow_credentials must be True for the browser to send/receive the
    # HttpOnly refresh-token cookie on cross-origin requests (the Vite dev
    # server and this API are different origins even when both run on
    # localhost) -- CORS forbids combining that with a wildcard origin, which
    # is already not used here.
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(NotFoundError)
def handle_not_found_error(request: Request, exc: NotFoundError) -> JSONResponse:
    """Map domain not-found errors to a 404 response."""
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ValidationError)
def handle_validation_error(request: Request, exc: ValidationError) -> JSONResponse:
    """Map domain validation errors to a 400 response."""
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(BusinessRuleError)
def handle_business_rule_error(
    request: Request, exc: BusinessRuleError
) -> JSONResponse:
    """Map business-rule infeasibility errors to a 422 response."""
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(PersistenceError)
def handle_persistence_error(request: Request, exc: PersistenceError) -> JSONResponse:
    """Map storage-layer errors to a 500 response."""
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(ExternalServiceError)
def handle_external_service_error(
    request: Request, exc: ExternalServiceError
) -> JSONResponse:
    """Map external-service failures (e.g. the Claude API) to a 502 response."""
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(AuthenticationError)
def handle_authentication_error(
    request: Request, exc: AuthenticationError
) -> JSONResponse:
    """Map missing/invalid credentials or tokens to a 401 response."""
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(AuthorizationError)
def handle_authorization_error(
    request: Request, exc: AuthorizationError
) -> JSONResponse:
    """Map access to a resource the caller doesn't own to a 403 response."""
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(RateLimitError)
def handle_rate_limit_error(request: Request, exc: RateLimitError) -> JSONResponse:
    """Map an exceeded rate limit (e.g. repeated failed logins) to a 429 response."""
    return JSONResponse(status_code=429, content={"detail": str(exc)})


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(expenses_router)
app.include_router(budgets_router)
app.include_router(accounts_router)
app.include_router(bills_router)
app.include_router(debt_router)
app.include_router(income_router)
app.include_router(goals_router)
app.include_router(history_router)
app.include_router(forecasting_router)
app.include_router(scenarios_router)
app.include_router(coach_router)
app.include_router(dashboard.router)
app.include_router(recommendations_router)
app.include_router(recurring_expenses_router)
app.include_router(notifications_router)
app.include_router(admin_router)
