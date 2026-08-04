"""
Application-wide exception hierarchy for the Financial Core application.

All custom exceptions subclass AppError, and AppError subclasses
ValueError so existing `except ValueError` / `pytest.raises(ValueError)`
call sites continue to work unchanged as bare ValueError raises are
migrated to these more specific types.
"""


class AppError(ValueError):
    """Base class for all application-specific domain errors."""


class ValidationError(AppError):
    """Raised when a domain object or input fails a validation rule."""


class NotFoundError(AppError):
    """Raised when a requested domain entity cannot be located."""


class BusinessRuleError(AppError):
    """Raised when an operation violates a business rule or is infeasible."""


class PersistenceError(AppError):
    """Raised when stored data is missing, malformed, or cannot be loaded."""


class ExternalServiceError(AppError):
    """Raised when a call to an external service fails or is unavailable."""


class AuthenticationError(AppError):
    """Raised when credentials are invalid or a token is missing/invalid/expired."""


class AuthorizationError(AppError):
    """Raised when an authenticated user attempts to access a resource they don't own."""


class RateLimitError(AppError):
    """Raised when a caller exceeds an allowed rate (e.g. repeated failed login attempts)."""


class StepUpRequiredError(AppError):
    """Raised when an action requires recent re-authentication ("step-up")
    that the caller's current session doesn't have -- distinct from
    AuthorizationError (which means the caller can never do this) since a
    fresh POST /auth/reauth is enough to satisfy it."""
