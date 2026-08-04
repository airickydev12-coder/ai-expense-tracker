"""API schemas for auth endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


class TokenResponse(BaseModel):
    """Response body containing an access token."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Serialized representation of a user, excluding the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
