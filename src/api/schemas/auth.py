"""API schemas for auth endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.financial.users.role import PlatformRole


class RegisterRequest(BaseModel):
    """Request body for registering a new user."""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Request body for logging in."""

    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class UpdateProfileRequest(BaseModel):
    """Request body for updating the current user's username and/or email."""

    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None


class ChangePasswordRequest(BaseModel):
    """Request body for changing the current user's password."""

    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    """Request body for requesting a password reset email."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request body for consuming a password reset token."""

    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    """Request body for consuming an email verification token."""

    token: str = Field(min_length=1)


class SessionResponse(BaseModel):
    """One active refresh-token-backed session, for the self-service sessions list.

    Deliberately excludes the token hash itself -- this is what the user
    sees, never anything that could be replayed.
    """

    id: int
    issued_at: datetime
    expires_at: datetime
    user_agent: str | None
    ip_address: str | None
    is_current: bool


class AccessTokenResponse(BaseModel):
    """Response body containing a fresh access token.

    The refresh token is never returned in a JSON body -- it's set as an
    HttpOnly cookie by the router instead, so client-side JavaScript can
    never read it (the whole point of the cookie-based refresh-token
    architecture over the earlier localStorage approach).
    """

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Serialized representation of a user, excluding the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    is_active: bool
    role: PlatformRole
    created_at: datetime
    updated_at: datetime
    email_verified: bool
