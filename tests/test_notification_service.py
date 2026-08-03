from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from src.core.exceptions import ExternalServiceError
from src.financial.bills.models import Bill
from src.financial.budgets.models import Budget
from src.financial.engine.financial_snapshot_builder import (
    build_financial_snapshot as build_real_snapshot,
)
from src.financial.expenses.models import Expense
from src.financial.notifications import service as notification_service
from src.financial.notifications.service import (
    check_and_send_notifications,
    get_next_notification_log_id,
    get_notification_log,
    notification_log,
)
from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.shared.categories import ExpenseCategory


def setup_function():
    """Clear notification log state before every test."""
    notification_log.clear()


def build_snapshot_with_bill_due_soon():
    bill = Bill(id=1, name="Electric", amount=Decimal("125.00"), due_day=17)
    return build_real_snapshot(
        income_entries=[],
        expenses=[],
        budgets=[],
        accounts=[],
        goals=[],
        debts=[],
        bills=[bill],
        current_day=15,
    )


def build_snapshot_with_budget_overrun():
    expenses = [
        Expense(id=1, name="Groceries", category=ExpenseCategory.FOOD, amount=Decimal("600.00"))
    ]
    budgets = [Budget(category=ExpenseCategory.FOOD, limit=Decimal("500.00"))]
    return build_real_snapshot(
        income_entries=[],
        expenses=expenses,
        budgets=budgets,
        accounts=[],
        goals=[],
        debts=[],
        bills=[],
        current_day=15,
    )


def build_empty_snapshot():
    return build_real_snapshot(
        income_entries=[],
        expenses=[],
        budgets=[],
        accounts=[],
        goals=[],
        debts=[],
        bills=[],
        current_day=15,
    )


def build_high_priority_recommendation() -> Recommendation:
    return Recommendation(
        priority=RecommendationPriority.HIGH,
        category=RecommendationCategory.DEBT,
        title="High Interest Debt",
        message="Card A has a high interest rate.",
        action="Prioritize this debt for repayment.",
        source_rule="HighInterestDebtRule",
    )


def _no_recommendations(priority=None, category=None, limit=None):
    return []


def test_sends_email_for_bill_due_soon(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    sent: dict = {}

    def fake_send(subject: str, body: str) -> None:
        sent["subject"] = subject
        sent["body"] = body

    monkeypatch.setattr(notification_service, "send_notification_email", fake_send)
    monkeypatch.setattr(
        notification_service, "build_financial_snapshot", build_snapshot_with_bill_due_soon
    )
    monkeypatch.setattr(notification_service, "build_recommendations", _no_recommendations)

    entries = check_and_send_notifications(
        as_of=date(2026, 9, 15),
        file_path=tmp_path / "notifications.db",
    )

    assert len(entries) == 1
    assert entries[0].status == "SENT"
    assert "Electric" in sent["body"]
    assert get_next_notification_log_id() == 2


def test_sends_email_for_budget_overrun(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    sent: dict = {}

    monkeypatch.setattr(
        notification_service,
        "send_notification_email",
        lambda subject, body: sent.update(subject=subject, body=body),
    )
    monkeypatch.setattr(
        notification_service, "build_financial_snapshot", build_snapshot_with_budget_overrun
    )
    monkeypatch.setattr(notification_service, "build_recommendations", _no_recommendations)

    entries = check_and_send_notifications(
        as_of=date(2026, 9, 15),
        file_path=tmp_path / "notifications.db",
    )

    assert len(entries) == 1
    assert "Food" in sent["body"]
    assert "over by" in sent["body"]


def test_sends_email_for_urgent_recommendation(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    sent: dict = {}

    monkeypatch.setattr(
        notification_service,
        "send_notification_email",
        lambda subject, body: sent.update(subject=subject, body=body),
    )
    monkeypatch.setattr(notification_service, "build_financial_snapshot", build_empty_snapshot)

    def fake_build_recommendations(priority=None, category=None, limit=None):
        if priority == "HIGH":
            return [build_high_priority_recommendation()]
        return []

    monkeypatch.setattr(
        notification_service, "build_recommendations", fake_build_recommendations
    )

    entries = check_and_send_notifications(
        as_of=date(2026, 9, 15),
        file_path=tmp_path / "notifications.db",
    )

    assert len(entries) == 1
    assert "High Interest Debt" in sent["body"]


def test_returns_empty_when_nothing_new(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(
        notification_service,
        "send_notification_email",
        lambda subject, body: pytest.fail("Should not send when there are no candidates"),
    )
    monkeypatch.setattr(notification_service, "build_financial_snapshot", build_empty_snapshot)
    monkeypatch.setattr(notification_service, "build_recommendations", _no_recommendations)

    entries = check_and_send_notifications(
        as_of=date(2026, 9, 15),
        file_path=tmp_path / "notifications.db",
    )

    assert entries == []


def test_skips_candidate_already_sent_today(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    call_count = {"n": 0}

    def fake_send(subject: str, body: str) -> None:
        call_count["n"] += 1

    monkeypatch.setattr(notification_service, "send_notification_email", fake_send)
    monkeypatch.setattr(
        notification_service, "build_financial_snapshot", build_snapshot_with_bill_due_soon
    )
    monkeypatch.setattr(notification_service, "build_recommendations", _no_recommendations)

    db_path = tmp_path / "notifications.db"
    first = check_and_send_notifications(as_of=date(2026, 9, 15), file_path=db_path)
    second = check_and_send_notifications(as_of=date(2026, 9, 15), file_path=db_path)

    assert len(first) == 1
    assert second == []
    assert call_count["n"] == 1


def test_records_failed_status_on_smtp_error_and_allows_retry(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    def failing_send(subject: str, body: str) -> None:
        raise ExternalServiceError("Failed to send notification email: boom")

    monkeypatch.setattr(notification_service, "send_notification_email", failing_send)
    monkeypatch.setattr(
        notification_service, "build_financial_snapshot", build_snapshot_with_bill_due_soon
    )
    monkeypatch.setattr(notification_service, "build_recommendations", _no_recommendations)

    db_path = tmp_path / "notifications.db"
    first = check_and_send_notifications(as_of=date(2026, 9, 15), file_path=db_path)
    assert len(first) == 1
    assert first[0].status == "FAILED"

    call_count = {"n": 0}

    def succeeding_send(subject: str, body: str) -> None:
        call_count["n"] += 1

    monkeypatch.setattr(notification_service, "send_notification_email", succeeding_send)

    second = check_and_send_notifications(as_of=date(2026, 9, 15), file_path=db_path)
    assert len(second) == 1
    assert second[0].status == "SENT"
    assert call_count["n"] == 1


def test_get_notification_log_returns_most_recent_first() -> None:
    notification_log.append(
        notification_service.NotificationLogEntry(
            id=1,
            notification_key="a",
            channel="EMAIL",
            subject="s",
            body="b",
            sent_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            status="SENT",
        )
    )
    notification_log.append(
        notification_service.NotificationLogEntry(
            id=2,
            notification_key="b",
            channel="EMAIL",
            subject="s",
            body="b",
            sent_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
            status="SENT",
        )
    )

    log = get_notification_log()

    assert [entry.id for entry in log] == [2, 1]
