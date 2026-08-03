"""Thin SMTP email delivery for the notification checker."""

import smtplib
from email.message import EmailMessage

from src.core import config
from src.core.exceptions import ExternalServiceError
from src.core.logging import get_logger

logger = get_logger(__name__)


def send_notification_email(subject: str, body: str, to_email: str | None = None) -> None:
    """
    Send one notification email via SMTP.

    `to_email` defaults to config.NOTIFICATION_TO_EMAIL for backward
    compatibility, but callers should pass the recipient user's own email
    once available (see notifications/service.py).

    Kept thin and separately monkeypatchable so tests never make a live
    network call. Raises ExternalServiceError on any SMTP/connection
    failure -- callers decide how to record that (see
    notifications/service.py, which catches this and logs a FAILED entry
    rather than letting it propagate out of a scheduled job).
    """
    recipient = to_email or config.NOTIFICATION_TO_EMAIL

    if not config.SMTP_HOST or not recipient:
        raise ExternalServiceError(
            "Email notifications are not configured "
            "(SMTP_HOST/NOTIFICATION_TO_EMAIL are unset)."
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config.SMTP_FROM_EMAIL or config.SMTP_USER or "noreply@localhost"
    message["To"] = recipient
    message.set_content(body)

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10) as smtp:
            smtp.starttls()
            if config.SMTP_USER and config.SMTP_PASSWORD:
                smtp.login(config.SMTP_USER, config.SMTP_PASSWORD)
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        logger.warning("Failed to send notification email: %s", exc)
        raise ExternalServiceError(f"Failed to send notification email: {exc}") from exc
