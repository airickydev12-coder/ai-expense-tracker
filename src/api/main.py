"""
Main FastAPI application.

This module creates the API application and registers
routers, middleware, exception handlers, and startup events.
"""

import logging

from fastapi import FastAPI

from src.api.routers import dashboard
from src.api.routers.budgets import router as budgets_router
from src.api.routers.expenses import router as expenses_router
from src.api.routers.health import router as health_router
from src.api.routers.recommendations import (
    router as recommendations_router,
)
from src.core.db import initialize_database
from src.core.logging import configure_logging

configure_logging(console_level=logging.INFO)
initialize_database()

app = FastAPI(
    title="AI Expense Tracker API",
    description="REST API for the AI Expense Tracker financial platform.",
    version="1.0.0",
)

app.include_router(health_router)
app.include_router(expenses_router)
app.include_router(budgets_router)
app.include_router(dashboard.router)
app.include_router(recommendations_router)
