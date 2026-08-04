"""Auth API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_current_user
from src.api.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from src.core.security import create_access_token
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
    """Authenticate a user and issue a JWT access token."""
    user = user_service.authenticate_user(
        username=request.username,
        password=request.password,
    )
    token = create_access_token(user_id=user.id, username=user.username)
    return TokenResponse(access_token=token)


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
