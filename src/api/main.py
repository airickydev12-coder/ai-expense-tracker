"""
Main FastAPI application.

This module creates the API application and registers
routers, middleware, exception handlers, and startup events.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routers import dashboard
from src.api.routers.accounts import router as accounts_router
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
from src.api.routers.recommendations import (
    router as recommendations_router,
)
from src.api.routers.scenarios import router as scenarios_router
from src.core.db import initialize_database
from src.core.exceptions import (
    BusinessRuleError,
    ExternalServiceError,
    NotFoundError,
    PersistenceError,
    ValidationError,
)
from src.core.logging import configure_logging
from src.financial.application.financial_state import load_financial_state
from src.financial.scenarios.factory import register_default_scenario_handlers

configure_logging(console_level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize the database and hydrate in-memory state on startup."""
    initialize_database()
    load_financial_state()
    register_default_scenario_handlers()
    yield


app = FastAPI(
    title="AI Expense Tracker API",
    description="REST API for the AI Expense Tracker financial platform.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=False,
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


app.include_router(health_router)
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
