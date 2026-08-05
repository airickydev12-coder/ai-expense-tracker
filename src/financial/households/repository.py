import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.core.config import DB_PATH
from src.core.db import get_connection
from src.core.exceptions import PersistenceError
from src.core.logging import get_logger
from src.financial.households.models import (
    AgeBand,
    GuardianChildRelationship,
    Household,
    HouseholdMembership,
    LearningProfile,
    RelationshipStatus,
)

logger = get_logger(__name__)


# --- households (row pattern) ---


def create_household(name: str, db_path: Path = DB_PATH) -> Household:
    """Insert a new household row."""
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            cursor = connection.execute(
                "INSERT INTO households (name, created_at, updated_at) VALUES (?, ?, ?)",
                (name, now, now),
            )
            household_id = cursor.lastrowid
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to create household in {db_path}") from error

    logger.debug("Created household %d (%s) in %s", household_id, name, db_path)

    created = get_household_by_id(household_id, db_path) if household_id is not None else None
    if created is None:
        raise PersistenceError(f"Failed to reload newly created household in {db_path}")
    return created


def get_household_by_id(household_id: int, db_path: Path = DB_PATH) -> Household | None:
    """Return a household by ID, or None if it doesn't exist."""
    try:
        with get_connection(db_path) as connection:
            row = connection.execute(
                "SELECT id, name, created_at, updated_at FROM households WHERE id = ?",
                (household_id,),
            ).fetchone()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load household {household_id} from {db_path}") from error

    return Household.from_dict(dict(row)) if row is not None else None


# --- household_memberships (collection pattern, partitioned by household_id) ---


def load_household_memberships_from_file(
    household_id: int, db_path: Path = DB_PATH
) -> list[HouseholdMembership]:
    """Load every membership row for one household."""
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                "SELECT household_id, user_id, household_role, joined_at "
                "FROM household_memberships WHERE household_id = ? ORDER BY joined_at",
                (household_id,),
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to load memberships for household {household_id} from {db_path}"
        ) from error

    memberships = [HouseholdMembership.from_dict(dict(row)) for row in rows]

    logger.debug(
        "Loaded %d membership(s) for household %d from %s", len(memberships), household_id, db_path
    )

    return memberships


def save_household_memberships_to_file(
    memberships: list[HouseholdMembership], household_id: int, db_path: Path = DB_PATH
) -> None:
    """Save a household's memberships, replacing its existing rows."""
    try:
        with get_connection(db_path) as connection:
            connection.execute(
                "DELETE FROM household_memberships WHERE household_id = ?", (household_id,)
            )
            connection.executemany(
                "INSERT INTO household_memberships (household_id, user_id, household_role, joined_at) "
                "VALUES (:household_id, :user_id, :household_role, :joined_at)",
                [membership.to_dict() for membership in memberships],
            )
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to save memberships for household {household_id} to {db_path}"
        ) from error

    logger.debug(
        "Saved %d membership(s) for household %d to %s", len(memberships), household_id, db_path
    )


def list_household_memberships_for_user(
    user_id: int, db_path: Path = DB_PATH
) -> list[HouseholdMembership]:
    """Return every membership row for a user, across all households.

    Deliberately bypasses the household_id-keyed cache in service.py --
    there's no way to know which households to load without this reverse
    query first (used for "list households for a user" / household
    selection).
    """
    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(
                "SELECT household_id, user_id, household_role, joined_at "
                "FROM household_memberships WHERE user_id = ? ORDER BY joined_at",
                (user_id,),
            ).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to load memberships for user {user_id} from {db_path}"
        ) from error

    return [HouseholdMembership.from_dict(dict(row)) for row in rows]


# --- guardian_child_relationships (row pattern) ---


def create_guardian_child_relationship(
    guardian_user_id: int,
    child_user_id: int,
    status: RelationshipStatus,
    db_path: Path = DB_PATH,
) -> GuardianChildRelationship:
    """Insert a new guardian-child relationship row."""
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            cursor = connection.execute(
                "INSERT INTO guardian_child_relationships "
                "(guardian_user_id, child_user_id, status, created_at) VALUES (?, ?, ?, ?)",
                (guardian_user_id, child_user_id, status.value, now),
            )
            relationship_id = cursor.lastrowid
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to create guardian-child relationship in {db_path}") from error

    logger.debug(
        "Created guardian-child relationship %d (guardian %d, child %d) in %s",
        relationship_id,
        guardian_user_id,
        child_user_id,
        db_path,
    )

    created = (
        get_relationship(guardian_user_id, child_user_id, db_path)
        if relationship_id is not None
        else None
    )
    if created is None:
        raise PersistenceError(f"Failed to reload newly created relationship in {db_path}")
    return created


def get_relationship(
    guardian_user_id: int, child_user_id: int, db_path: Path = DB_PATH
) -> GuardianChildRelationship | None:
    """Return the (guardian, child) relationship row, or None if none exists.

    If more than one row exists for the pair (e.g. a revoked-then-recreated
    relationship), returns the most recent one.
    """
    try:
        with get_connection(db_path) as connection:
            row = connection.execute(
                "SELECT id, guardian_user_id, child_user_id, status, created_at, revoked_at "
                "FROM guardian_child_relationships "
                "WHERE guardian_user_id = ? AND child_user_id = ? ORDER BY id DESC LIMIT 1",
                (guardian_user_id, child_user_id),
            ).fetchone()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load guardian-child relationship from {db_path}") from error

    return GuardianChildRelationship.from_dict(dict(row)) if row is not None else None


def list_relationships_for_guardian(
    guardian_user_id: int,
    status: RelationshipStatus | None = None,
    db_path: Path = DB_PATH,
) -> list[GuardianChildRelationship]:
    """Return a guardian's relationships, optionally filtered by status."""
    query = (
        "SELECT id, guardian_user_id, child_user_id, status, created_at, revoked_at "
        "FROM guardian_child_relationships WHERE guardian_user_id = ?"
    )
    params: list = [guardian_user_id]

    if status is not None:
        query += " AND status = ?"
        params.append(status.value)

    query += " ORDER BY created_at"

    try:
        with get_connection(db_path) as connection:
            rows = connection.execute(query, params).fetchall()
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to load relationships for guardian {guardian_user_id} from {db_path}"
        ) from error

    return [GuardianChildRelationship.from_dict(dict(row)) for row in rows]


def revoke_all_relationships_for_child(child_user_id: int, db_path: Path = DB_PATH) -> None:
    """Flip every non-revoked relationship row for a child to REVOKED.

    Used only by request_adult_transition() -- age transition atomically
    (in intent) ends every guardian's visibility into the (former) child in
    the same action that flips account_type to ADULT (see ADR-007's Age
    Transition Q2). Idempotent: calling this twice is a no-op the second
    time.
    """
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            connection.execute(
                "UPDATE guardian_child_relationships SET status = ?, revoked_at = ? "
                "WHERE child_user_id = ? AND status != ?",
                (RelationshipStatus.REVOKED.value, now, child_user_id, RelationshipStatus.REVOKED.value),
            )
    except sqlite3.Error as error:
        raise PersistenceError(
            f"Failed to revoke relationships for child {child_user_id} in {db_path}"
        ) from error

    logger.debug("Revoked all guardian relationships for child %d in %s", child_user_id, db_path)


# --- learning_profiles (row pattern, genuinely 1:1 on user_id) ---


def create_learning_profile(
    user_id: int,
    age_band: AgeBand,
    ai_coach_enabled: bool,
    db_path: Path = DB_PATH,
) -> LearningProfile:
    """Insert a new learning profile row for a MINOR account."""
    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection(db_path) as connection:
            connection.execute(
                "INSERT INTO learning_profiles (user_id, age_band, ai_coach_enabled, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, age_band.value, int(ai_coach_enabled), now, now),
            )
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to create learning profile for user {user_id} in {db_path}") from error

    logger.debug("Created learning profile for user %d in %s", user_id, db_path)

    created = get_learning_profile(user_id, db_path)
    if created is None:
        raise PersistenceError(f"Failed to reload newly created learning profile in {db_path}")
    return created


def get_learning_profile(user_id: int, db_path: Path = DB_PATH) -> LearningProfile | None:
    """Return a user's learning profile, or None if none exists."""
    try:
        with get_connection(db_path) as connection:
            row = connection.execute(
                "SELECT user_id, age_band, ai_coach_enabled, created_at, updated_at "
                "FROM learning_profiles WHERE user_id = ?",
                (user_id,),
            ).fetchone()
    except sqlite3.Error as error:
        raise PersistenceError(f"Failed to load learning profile for user {user_id} from {db_path}") from error

    return LearningProfile.from_dict(dict(row)) if row is not None else None
