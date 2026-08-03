"""Tests for CSV export of the AI-generated monthly financial review."""

import csv
import io
from decimal import Decimal

import pytest

from src.core.exceptions import BusinessRuleError
from src.financial.coach.monthly_review_export import export_monthly_review_to_csv


def build_ok_review() -> dict:
    return {
        "status": "ok",
        "period_start": "2026-08-01T00:00:00+00:00",
        "period_end": "2026-08-31T00:00:00+00:00",
        "overall_summary": "Overall summary.",
        "income_vs_expenses": {
            "narrative": "Income narrative.",
            "income_change": Decimal("100.00"),
            "expense_change": Decimal("-50.00"),
        },
        "cash_flow": {
            "narrative": "Cash flow narrative.",
            "change": Decimal("150.00"),
            "direction": "Improving",
        },
        "debt_progress": {
            "narrative": "Debt narrative.",
            "total_debt": Decimal("1000.00"),
        },
        "savings_progress": {"narrative": "Savings narrative."},
        "goal_status": {"narrative": "Goals narrative."},
        "health_score": {
            "narrative": "Health score narrative.",
            "change": 5,
            "direction": "Improving",
            "current_score": 80,
        },
        "top_actions": [
            {
                "key": "debt:high_interest_debt",
                "title": "High Interest Debt",
                "message": "Card A has a high interest rate.",
                "action": "Prioritize this debt for repayment.",
                "priority": "HIGH",
            }
        ],
        "category_trends": [
            {"category": "Food", "change": Decimal("60.00"), "direction": "Increasing"}
        ],
        "known_gaps": [],
    }


def _rows(csv_text: str) -> list[list[str]]:
    return list(csv.reader(io.StringIO(csv_text)))


def test_export_monthly_review_to_csv_includes_all_sections():
    csv_text = export_monthly_review_to_csv(build_ok_review())
    rows = _rows(csv_text)

    assert rows[0] == ["section", "field", "value"]
    assert ["Overview", "overall_summary", "Overall summary."] in rows
    assert ["Income vs Expenses", "income_change", "100.00"] in rows
    assert ["Cash Flow", "direction", "Improving"] in rows
    assert ["Debt Progress", "total_debt", "1000.00"] in rows
    assert ["Savings Progress", "narrative", "Savings narrative."] in rows
    assert ["Goal Status", "narrative", "Goals narrative."] in rows
    assert ["Health Score", "current_score", "80"] in rows
    assert [
        "Top Action",
        "HIGH: High Interest Debt",
        "Card A has a high interest rate.",
    ] in rows
    assert ["Category Trend", "Food", "Increasing (60.00)"] in rows


def test_export_monthly_review_to_csv_includes_known_gaps():
    review = build_ok_review()
    review["known_gaps"] = ["Category trend data is not yet available."]

    rows = _rows(export_monthly_review_to_csv(review))

    assert ["Known Gap", "", "Category trend data is not yet available."] in rows


@pytest.mark.parametrize(
    "status",
    ["no_history", "insufficient_recent_history"],
)
def test_export_monthly_review_to_csv_rejects_degraded_status(status: str):
    with pytest.raises(BusinessRuleError, match="No monthly review is available"):
        export_monthly_review_to_csv({"status": status, "message": "Not enough data."})
