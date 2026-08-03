from datetime import date, datetime, timezone
from pathlib import Path

from src.core.config import DB_PATH
from src.core.exceptions import ExternalServiceError
from src.core.logging import get_logger
from src.financial.application.financial_snapshot_service import (
    build_financial_snapshot,
)
from src.financial.application.recommendation_application_service import (
    build_recommendations,
)
from src.financial.bills.analytics import get_bills_due_soon
from src.financial.notifications.email_sender import send_notification_email
from src.financial.notifications.models import NotificationLogEntry
from src.financial.notifications.repository import (
    load_notification_log_from_file,
    save_notification_log_to_file,
)

logger = get_logger(__name__)

notification_log: dict[int, list[NotificationLogEntry]] = {}


def _ensure_loaded(user_id: int, db_path: Path = DB_PATH) -> None:
    """Lazily load a user's notification log into the cache on first access."""
    if user_id not in notification_log:
        notification_log[user_id] = load_notification_log_from_file(user_id, db_path)


def load_notification_log(user_id: int, file_path: Path = DB_PATH) -> None:
    """Load a user's notification log into application memory."""
    notification_log[user_id] = load_notification_log_from_file(user_id, file_path)


def save_notification_log(user_id: int, file_path: Path = DB_PATH) -> None:
    """Save a user's notification log from application memory."""
    save_notification_log_to_file(notification_log[user_id], user_id, file_path)


def get_notification_log(user_id: int, db_path: Path = DB_PATH) -> list[NotificationLogEntry]:
    """Return a copy of a user's notification log, most recent first."""
    _ensure_loaded(user_id, db_path)
    return sorted(notification_log[user_id], key=lambda entry: entry.sent_at, reverse=True)


def get_next_notification_log_id(user_id: int) -> int:
    """Return the next available notification log entry ID for this user."""
    user_log = notification_log.get(user_id, [])
    if not user_log:
        return 1

    return max(entry.id for entry in user_log) + 1


def _already_sent(user_id: int, notification_key: str) -> bool:
    """
    Return whether a notification_key has already been *successfully* sent
    to this user.

    Only SENT entries block a resend -- a FAILED attempt (e.g. a transient
    SMTP outage) is deliberately eligible to retry on the next check.
    `notification_key` is itself date-scoped (see _collect_candidates), so
    checking key + status alone is sufficient -- no separate date comparison
    is needed (and comparing against entry.sent_at's real wall-clock time
    would be wrong when `as_of` is backdated, e.g. in tests). Scoped by
    user_id so two different users' identical candidate on the same day
    (e.g. both have a bill with the same id due) don't suppress each other.
    """
    return any(
        entry.notification_key == notification_key and entry.status == "SENT"
        for entry in notification_log.get(user_id, [])
    )


def _collect_candidates(user_id: int, as_of: date) -> list[tuple[str, str]]:
    """
    Return (notification_key, description) pairs for every currently
    actionable signal -- bills due soon, over-budget categories, and
    critical/high-priority recommendations.

    Reuses the existing analytics/recommendation functions directly rather
    than the single-match rules/*.py versions (each of which only surfaces
    its first match), so every qualifying item gets its own candidate.
    """
    snapshot = build_financial_snapshot(user_id)
    today_key = as_of.isoformat()
    candidates: list[tuple[str, str]] = []

    for bill in get_bills_due_soon(snapshot.bills, snapshot.current_day):
        key = f"bill_due:{bill.id}:{today_key}"
        candidates.append(
            (key, f"Bill due soon: {bill.name} (${bill.amount}, due day {bill.due_day})")
        )

    for item in snapshot.budget_report:
        if item["remaining"] < 0:
            key = f"budget_overrun:{item['category']}:{today_key}"
            candidates.append(
                (
                    key,
                    f"Budget over: {item['category']} is over by "
                    f"${abs(item['remaining']):.2f}",
                )
            )

    urgent_recommendations = build_recommendations(
        user_id, priority="CRITICAL"
    ) + build_recommendations(user_id, priority="HIGH")
    for recommendation in urgent_recommendations:
        key = f"recommendation:{recommendation.key}:{today_key}"
        candidates.append((key, f"{recommendation.priority.name}: {recommendation.title}"))

    return candidates


def check_and_send_notifications(
    user_id: int,
    to_email: str | None = None,
    as_of: date | None = None,
    file_path: Path = DB_PATH,
) -> list[NotificationLogEntry]:
    """
    Check for actionable financial signals and email any new ones to this user.

    Independently callable and testable with zero scheduler involvement --
    the scheduler (wired in src/api/main.py) iterates every registered user
    and calls this once per user on an interval. SMTP failures are caught
    here and recorded as a FAILED log entry rather than propagating, so one
    bad send never breaks the periodic job or another user's check.
    """
    _ensure_loaded(user_id, file_path)

    effective_date = as_of if as_of is not None else date.today()

    candidates = _collect_candidates(user_id, effective_date)
    new_candidates = [
        (key, description)
        for key, description in candidates
        if not _already_sent(user_id, key)
    ]

    if not new_candidates:
        logger.info(
            "No new notification candidates for user %d as of %s",
            user_id,
            effective_date.isoformat(),
        )
        return []

    subject = f"Financial Tracker: {len(new_candidates)} item(s) need your attention"
    body = "\n".join(description for _, description in new_candidates)

    now = datetime.now(timezone.utc)
    new_entries: list[NotificationLogEntry] = []

    try:
        send_notification_email(subject, body, to_email)
        status = "SENT"
    except ExternalServiceError as exc:
        logger.warning("Notification email delivery failed for user %d: %s", user_id, exc)
        status = "FAILED"

    for key, _description in new_candidates:
        entry = NotificationLogEntry(
            id=get_next_notification_log_id(user_id),
            notification_key=key,
            channel="EMAIL",
            subject=subject,
            body=body,
            sent_at=now,
            status=status,
        )
        notification_log[user_id].append(entry)
        new_entries.append(entry)

    save_notification_log(user_id, file_path)

    logger.info(
        "Notification check for user %d as of %s: %d new candidate(s), status=%s",
        user_id,
        effective_date.isoformat(),
        len(new_candidates),
        status,
    )

    return new_entries
