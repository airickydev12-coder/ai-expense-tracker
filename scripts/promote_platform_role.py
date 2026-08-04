"""
Explicit, one-time-per-account promotion of a user to an elevated platform
role (ADMIN or SUPER_ADMIN).

Deliberately not automatic: unlike scripts/backfill_user_id.py's fixed "me"
target, there's no single account that's correct to promote across every
database this app runs against (the local dev DB and a deployed DB can have
different first-registered users, including throwaway test accounts) --
so the operator names the account explicitly.

Records one admin_audit_events row for the promotion (actor_user_id=NULL,
since a bootstrap promotion by definition has no acting admin yet).

Run from the repo root as a module (so `src` resolves on sys.path):

    .venv/Scripts/python.exe -m scripts.promote_platform_role <username> <role>

Example:

    .venv/Scripts/python.exe -m scripts.promote_platform_role me super_admin
"""

from __future__ import annotations

import sys

from src.core.db import initialize_database
from src.financial.users.repository import (
    create_admin_audit_event,
    get_user_by_username,
    update_user_role,
)
from src.financial.users.role import PlatformRole


def promote(username: str, role: PlatformRole) -> None:
    """Promote an existing user to the given platform role."""
    initialize_database()

    user = get_user_by_username(username)
    if user is None:
        raise SystemExit(f"No user found with username '{username}'.")

    if user.role == role:
        print(f"User '{username}' (id={user.id}) already has role '{role.value}'. No change made.")
        return

    previous_role = user.role
    updated = update_user_role(user.id, role)

    create_admin_audit_event(
        actor_user_id=None,
        action="role.assign",
        target_type="user",
        target_id=str(updated.id),
        reason=f"Promoted via promote_platform_role.py script (was '{previous_role.value}').",
        metadata={"previous_role": previous_role.value, "new_role": role.value},
    )

    print(f"Promoted '{username}' (id={updated.id}) from '{previous_role.value}' to '{role.value}'.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: python -m scripts.promote_platform_role <username> <role>\n"
            f"Valid roles: {', '.join(r.value for r in PlatformRole)}"
        )

    target_username, target_role_value = sys.argv[1], sys.argv[2]

    try:
        target_role = PlatformRole(target_role_value)
    except ValueError:
        raise SystemExit(
            f"Invalid role '{target_role_value}'. "
            f"Valid roles: {', '.join(r.value for r in PlatformRole)}"
        ) from None

    promote(target_username, target_role)
