"""Auth API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from src.api.dependencies import get_current_user, require_recent_auth
from src.api.schemas.auth import (
    AccessTokenResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ReauthRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SessionResponse,
    UpdateProfileRequest,
    UserResponse,
    VerifyEmailRequest,
)
from src.core.config import COOKIE_SECURE, REFRESH_TOKEN_COOKIE_NAME, REFRESH_TOKEN_EXPIRY_DAYS
from src.core.exceptions import AuthenticationError
from src.financial.users import service as user_service
from src.financial.users.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])

_REFRESH_TOKEN_MAX_AGE_SECONDS = REFRESH_TOKEN_EXPIRY_DAYS * 24 * 60 * 60


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Set the refresh token as an HttpOnly cookie -- never exposed to JS.

    path="/" deliberately, not scoped to "/auth": in the Docker deployment,
    nginx proxies the browser-visible path /api/auth/* to this router's own
    /auth/* path, so a cookie scoped to "/auth" would never actually match
    the request paths the browser sends it on.
    """
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        max_age=_REFRESH_TOKEN_MAX_AGE_SECONDS,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE_NAME, path="/")


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/register", response_model=UserResponse, status_code=201)
def register(request: RegisterRequest) -> UserResponse:
    """Register a new user account."""
    user = user_service.register_user(
        username=request.username,
        email=request.email,
        password=request.password,
    )
    return UserResponse.model_validate(user)


@router.post("/login", response_model=AccessTokenResponse)
def login(request: LoginRequest, http_request: Request, response: Response) -> AccessTokenResponse:
    """Authenticate a user, set a refresh-token cookie, and return an access token."""
    user = user_service.authenticate_user(
        username=request.username,
        password=request.password,
    )
    user_agent = http_request.headers.get("user-agent")
    ip_address = _client_ip(http_request)
    user_service.notify_new_device_if_needed(user, user_agent, ip_address)
    access_token, refresh_token = user_service.issue_session(
        user.id,
        user.username,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    _set_refresh_cookie(response, refresh_token)
    return AccessTokenResponse(access_token=access_token)


@router.post("/reauth", response_model=AccessTokenResponse)
def reauth(
    request: Request,
    body: ReauthRequest,
    current_user: User = Depends(get_current_user),
) -> AccessTokenResponse:
    """Re-verify the current user's password and mint a fresh access token
    with a fresh auth_time -- clears a StepUpRequiredError so a previously-
    rejected sensitive action can be retried."""
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    access_token = user_service.reauth(current_user.id, body.password, refresh_token=refresh_token)
    return AccessTokenResponse(access_token=access_token)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(request: Request, response: Response) -> AccessTokenResponse:
    """Exchange the refresh-token cookie for a new access token, rotating the cookie."""
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    if not refresh_token:
        raise AuthenticationError("Missing refresh token cookie.")

    access_token, new_refresh_token = user_service.refresh_session(
        refresh_token,
        user_agent=request.headers.get("user-agent"),
        ip_address=_client_ip(request),
    )
    _set_refresh_cookie(response, new_refresh_token)
    return AccessTokenResponse(access_token=access_token)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response) -> None:
    """Log out by revoking the refresh-token cookie's session and clearing the cookie.

    No longer requires a bearer access token: that requirement previously
    existed to stop a caller from blindly revoking an arbitrary refresh-token
    *string* belonging to someone else, but the cookie is never readable by
    JavaScript now, so there's no string to forge -- the browser can only
    ever send back its own cookie. A missing or already-invalid cookie is
    treated as an idempotent no-op (still 204), matching "log out" being
    safe to call on a session that's already ended.
    """
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    if refresh_token:
        user_service.logout(refresh_token)
    _clear_refresh_cookie(response)


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


@router.post("/verify-email", status_code=204)
def verify_email(request: VerifyEmailRequest) -> None:
    """Consume an email verification token. Public -- the token itself is the credential,
    the same way password-reset tokens work, since the link may be opened on a device/
    browser that was never logged in."""
    user_service.verify_email(token=request.token)


@router.post("/resend-verification", status_code=202)
def resend_verification(current_user: User = Depends(get_current_user)) -> None:
    """Resend the current user's verification email. Rate-limited."""
    user_service.resend_verification_email(current_user.id)


@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """List the current user's active sessions (refresh-token-backed)."""
    current_refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    return user_service.list_sessions(current_user.id, current_refresh_token)


@router.delete("/sessions/{session_id}", status_code=204)
def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
) -> None:
    """Revoke one of the current user's own sessions by id."""
    user_service.revoke_session(current_user.id, session_id)


@router.post("/sessions/revoke-all", status_code=204)
def revoke_all_sessions(response: Response, current_user: User = Depends(require_recent_auth)) -> None:
    """Log out of every session/device for the current user, including this one.

    Also clears this request's own refresh-token cookie, since the session
    it belongs to is revoked along with every other one.
    """
    user_service.logout_all_sessions(current_user.id)
    _clear_refresh_cookie(response)
