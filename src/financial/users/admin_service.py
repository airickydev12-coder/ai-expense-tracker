"""Admin-only orchestration over user accounts: listing, activation,
platform-role assignment, and session revocation.

Deliberately separate from service.py, which is exclusively self-service
(a user acting on their own account). Every function here acts on a
*target* account on behalf of an *actor* admin, and records an
admin_audit_events row for the action -- see ADR-noted rationale in
scripts/promote_platform_role.py for why role assignment in particular
needs its own tracked code path rather than reusing that script's.
"""

from pathlib import Path

from src.core.config import DB_PATH
from src.core.exceptions import NotFoundError, ValidationError
from src.core.logging import get_logger
from src.financial.users.models import User
from src.financial.users.repository import (
    create_admin_audit_event,
    get_user_by_id,
    list_users as list_users_from_repository,
    revoke_all_refresh_tokens_for_user,
    update_user_active_status,
    update_user_role,
)
from src.financial.users.role import PlatformRole

logger = get_logger(__name__)


def list_users(db_path: Path = DB_PATH) -> list[User]:
    """Return every user account, active or not."""
    return list_users_from_repository(db_path)


def get_user_detail(user_id: int, db_path: Path = DB_PATH) -> User:
    """Return the user with the given id, or raise NotFoundError."""
    user = get_user_by_id(user_id, db_path)

    if user is None:
        raise NotFoundError(f"No user found with ID {user_id}.")

    return user


def set_user_active_status(
    actor: User,
    target_user_id: int,
    is_active: bool,
    db_path: Path = DB_PATH,
) -> User:
    """Activate or deactivate a user account.

    Deactivating also revokes every refresh token the account holds, so it
    can't keep minting new sessions after being cut off -- otherwise
    "deactivate" would only block future logins while doing nothing about a
    session already in progress. An admin can't deactivate their own
    account this way (guards against an accidental self-lockout with no
    other admin present to undo it).
    """
    if not is_active and target_user_id == actor.id:
        raise ValidationError("You cannot deactivate your own account.")

    target = get_user_detail(target_user_id, db_path)
    updated = update_user_active_status(target_user_id, is_active, db_path)

    if not is_active:
        revoke_all_refresh_tokens_for_user(target_user_id, db_path)

    create_admin_audit_event(
        actor_user_id=actor.id,
        action="user.activate" if is_active else "user.deactivate",
        target_type="user",
        target_id=str(target_user_id),
        metadata={"previous_is_active": target.is_active, "new_is_active": is_active},
        db_path=db_path,
    )

    logger.info(
        "Admin %d set active status for user %d to %s", actor.id, target_user_id, is_active
    )

    return updated


def assign_role(
    actor: User,
    target_user_id: int,
    new_role: PlatformRole,
    db_path: Path = DB_PATH,
) -> User:
    """Assign a user's platform role.

    An admin can't change their own role this way (guards against
    accidental self-demotion or self-escalation) -- gated behind
    require_super_admin at the router level, since this is the stricter of
    the two admin-console actions.
    """
    if target_user_id == actor.id:
        raise ValidationError("You cannot change your own role.")

    target = get_user_detail(target_user_id, db_path)
    previous_role = target.role
    updated = update_user_role(target_user_id, new_role, db_path)

    create_admin_audit_event(
        actor_user_id=actor.id,
        action="role.assign",
        target_type="user",
        target_id=str(target_user_id),
        metadata={"previous_role": previous_role.value, "new_role": new_role.value},
        db_path=db_path,
    )

    logger.info(
        "Admin %d assigned role %s to user %d (was %s)",
        actor.id,
        new_role.value,
        target_user_id,
        previous_role.value,
    )

    return updated


def revoke_user_sessions(actor: User, target_user_id: int, db_path: Path = DB_PATH) -> None:
    """Revoke every refresh token belonging to a user, ending all their sessions."""
    get_user_detail(target_user_id, db_path)
    revoke_all_refresh_tokens_for_user(target_user_id, db_path)

    create_admin_audit_event(
        actor_user_id=actor.id,
        action="session.revoke_all",
        target_type="user",
        target_id=str(target_user_id),
        db_path=db_path,
    )

    logger.info("Admin %d revoked all sessions for user %d", actor.id, target_user_id)
