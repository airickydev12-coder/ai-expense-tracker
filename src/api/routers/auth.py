"""Auth API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_current_user
from src.api.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from src.financial.users import service as user_service
from src.financial.users.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(request: RegisterRequest) -> UserResponse:
    """Register a new user account."""
    user = user_service.register_user(
        username=request.username,
        email=request.email,
        password=request.password,
    )
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest) -> TokenResponse:
    """Authenticate a user and issue an access token + refresh token."""
    user = user_service.authenticate_user(
        username=request.username,
        password=request.password,
    )
    access_token, refresh_token = user_service.issue_session(user.id, user.username)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshRequest) -> TokenResponse:
    """Exchange a refresh token for a new access token + refresh token (rotated)."""
    access_token, refresh_token = user_service.refresh_session(request.refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=204)
def logout(
    request: LogoutRequest,
    current_user: User = Depends(get_current_user),
) -> None:
    """Log out by revoking the given refresh token (current session only).

    Requires a valid bearer access token so this can't be used to blindly
    revoke an arbitrary refresh token string belonging to someone else.
    """
    user_service.logout(request.refresh_token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
def update_me(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Update the currently authenticated user's username and/or email."""
    if request.username is None and request.email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided.",
        )
    user = user_service.update_profile(
        current_user.id,
        username=request.username,
        email=request.email,
    )
    return UserResponse.model_validate(user)


@router.post("/change-password", status_code=204)
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
) -> None:
    """Change the currently authenticated user's password."""
    user_service.change_password(
        current_user.id,
        current_password=request.current_password,
        new_password=request.new_password,
    )


@router.post("/forgot-password", status_code=202)
def forgot_password(request: ForgotPasswordRequest) -> None:
    """Request a password reset email.

    Always returns 202 regardless of whether the email matches an account,
    so the response can't be used to enumerate registered emails.
    """
    user_service.request_password_reset(email=request.email)


@router.post("/reset-password", status_code=204)
def reset_password(request: ResetPasswordRequest) -> None:
    """Consume a password reset token and set a new password."""
    user_service.reset_password(token=request.token, new_password=request.new_password)
