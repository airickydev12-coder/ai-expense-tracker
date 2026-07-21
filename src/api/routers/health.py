"""
Health check endpoints.

These endpoints allow users, load balancers, and monitoring systems
to verify that the API is running.
"""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Return the API health status."""

    return {
        "status": "healthy",
        "service": "AI Expense Tracker API",
        "version": "1.0.0",
    }
