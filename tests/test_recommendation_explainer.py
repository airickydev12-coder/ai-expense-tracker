"""Tests for AI-generated, evidence-grounded recommendation explanations."""

from decimal import Decimal

import anthropic
import httpx
import pytest

from src.core.exceptions import ExternalServiceError, NotFoundError
from src.financial.coach import recommendation_explainer
from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority


def build_recommendation(
    category: RecommendationCategory,
    title: str,
    message: str,
    source_rule: str,
) -> Recommendation:
    return Recommendation(
        priority=RecommendationPriority.HIGH,
        category=category,
        title=title,
        message=message,
        action="Take action.",
        source_rule=source_rule,
    )


def build_debt_recommendation(
    source_rule: str = "HighInterestDebtRule",
    message: str = "Card A has a high interest rate of 27.40%.",
) -> Recommendation:
    return build_recommendation(
        RecommendationCategory.DEBT, "High Interest Debt", message, source_rule
    )


def build_snapshot(**overrides: object) -> dict:
    snapshot = {
        "total_income": Decimal("5000.00"),
        "total_expenses": Decimal("3000.00"),
        "net_cash_flow": Decimal("300.00"),
        "total_account_balance": Decimal("2000.00"),
        "total_goal_progress": Decimal("500.00"),
        "total_debt": Decimal("4800.00"),
        "net_worth": Decimal("5000.00"),
        "health_score": 70,
        "health_status": "Good",
        "current_day": 15,
        "debts": [
            {
                "id": 1,
                "name": "Card A",
                "balance": Decimal("4800.00"),
                "interest_rate": 27.4,
                "minimum_payment": Decimal("145.00"),
            }
        ],
        "goals": [
            {
                "id": 1,
                "name": "Emergency Fund",
                "target_amount": Decimal("10000.00"),
                "current_amount": Decimal("1000.00"),
            }
        ],
        "bills": [
            {
                "id": 1,
                "name": "Electric",
                "amount": Decimal("125.00"),
                "due_day": 18,
                "is_paid": False,
            }
        ],
        "budget_report": [
            {
                "category": "Food",
                "limit": Decimal("400.00"),
                "spent": Decimal("450.00"),
                "remaining": Decimal("-50.00"),
            }
        ],
        "largest_expense": {
            "id": 1,
            "name": "Rent",
            "category": "Housing",
            "amount": Decimal("1200.00"),
        },
        "average_expense": Decimal("300.00"),
        "category_totals": {
            "Housing": Decimal("1200.00"),
            "Food": Decimal("450.00"),
        },
    }
    snapshot.update(overrides)
    return snapshot


def test_explain_recommendation_raises_not_found_for_unknown_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unknown recommendation key should raise NotFoundError."""
    monkeypatch.setattr(
        recommendation_explainer,
        "get_recommendation_by_key",
        lambda key: None,
    )

    with pytest.raises(NotFoundError):
        recommendation_explainer.explain_recommendation("debt:unknown")


def test_explain_recommendation_returns_structured_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A DEBT recommendation should produce evidence-grounded structured output."""
    recommendation = build_debt_recommendation()
    snapshot = build_snapshot()

    monkeypatch.setattr(
        recommendation_explainer,
        "get_recommendation_by_key",
        lambda key: recommendation,
    )
    monkeypatch.setattr(
        recommendation_explainer,
        "build_current_financial_snapshot",
        lambda: snapshot,
    )
    monkeypatch.setattr(
        recommendation_explainer,
        "_request_explanation",
        lambda prompt: {
            "reason": "Card A has the highest APR.",
            "expected_impact": "Payoff sooner with lower interest cost.",
            "confidence": "High",
            "assumptions": ["Income remains stable."],
        },
    )

    result = recommendation_explainer.explain_recommendation(recommendation.key)

    assert result["recommendation_key"] == recommendation.key
    assert result["reason"] == "Card A has the highest APR."
    assert result["confidence"] == "High"
    assert result["evidence"]["type"] == "debt"
    assert result["evidence"]["debt_name"] == "Card A"
    assert result["evidence"]["payoff_months_saved"] is not None
    assert result["evidence"]["total_debt"] == Decimal("4800.00")


def test_get_recommendation_evidence_returns_no_ai_call_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Evidence lookup should return real data without any AI call."""
    recommendation = build_debt_recommendation()
    snapshot = build_snapshot()

    monkeypatch.setattr(
        recommendation_explainer,
        "get_recommendation_by_key",
        lambda key: recommendation,
    )
    monkeypatch.setattr(
        recommendation_explainer,
        "build_current_financial_snapshot",
        lambda: snapshot,
    )

    def fail_if_called(prompt: str) -> dict:
        raise AssertionError("get_recommendation_evidence must not call the AI.")

    monkeypatch.setattr(
        recommendation_explainer,
        "_request_explanation",
        fail_if_called,
    )

    result = recommendation_explainer.get_recommendation_evidence(recommendation.key)

    assert result["recommendation"]["key"] == recommendation.key
    assert result["evidence"]["type"] == "debt"
    assert result["evidence"]["debt_name"] == "Card A"


def test_get_recommendation_evidence_raises_not_found_for_unknown_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unknown recommendation key should raise NotFoundError."""
    monkeypatch.setattr(
        recommendation_explainer,
        "get_recommendation_by_key",
        lambda key: None,
    )

    with pytest.raises(NotFoundError):
        recommendation_explainer.get_recommendation_evidence("debt:unknown")


def test_choose_extra_payment_respects_cash_flow() -> None:
    """The chosen payment should be the largest affordable default candidate."""
    assert recommendation_explainer._choose_extra_payment(Decimal("300.00")) == 250.0
    assert recommendation_explainer._choose_extra_payment(Decimal("1000.00")) == 500.0
    assert recommendation_explainer._choose_extra_payment(Decimal("50.00")) == 100.0


def test_request_explanation_wraps_anthropic_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An Anthropic API failure should be wrapped in ExternalServiceError."""

    class FakeMessages:
        def create(self, **kwargs: object) -> None:
            raise anthropic.APIConnectionError(
                message="Connection error.",
                request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
            )

    class FakeClient:
        messages = FakeMessages()

    monkeypatch.setattr(
        recommendation_explainer.ai_client,
        "get_client",
        lambda: FakeClient(),
    )

    with pytest.raises(ExternalServiceError):
        recommendation_explainer._request_explanation("prompt")


# --- _gather_evidence: one real case per entity type ------------------------


def test_gather_evidence_for_goal_completion() -> None:
    recommendation = build_recommendation(
        RecommendationCategory.GOALS,
        "Goal Completed",
        "Your goal 'Emergency Fund' is fully funded.",
        "GoalCompletionRule",
    )
    snapshot = build_snapshot(
        goals=[
            {
                "id": 1,
                "name": "Emergency Fund",
                "target_amount": Decimal("1000.00"),
                "current_amount": Decimal("1000.00"),
            }
        ]
    )

    evidence = recommendation_explainer._gather_evidence(recommendation, snapshot)

    assert evidence["type"] == "goal"
    assert evidence["goal_name"] == "Emergency Fund"
    assert evidence["progress_percentage"] == 100.0


def test_gather_evidence_for_low_goal_progress() -> None:
    recommendation = build_recommendation(
        RecommendationCategory.GOALS,
        "Low Goal Progress",
        "Your goal 'Emergency Fund' is 10% funded.",
        "GoalProgressThresholdRule",
    )
    snapshot = build_snapshot()

    evidence = recommendation_explainer._gather_evidence(recommendation, snapshot)

    assert evidence["type"] == "goal"
    assert evidence["goal_name"] == "Emergency Fund"
    assert evidence["progress_percentage"] == 10.0


def test_gather_evidence_for_bill_due_soon() -> None:
    recommendation = build_recommendation(
        RecommendationCategory.BILLS,
        "Bill Due Soon",
        "Electric is due in 3 days.",
        "BillDueSoonRule",
    )
    snapshot = build_snapshot()

    evidence = recommendation_explainer._gather_evidence(recommendation, snapshot)

    assert evidence["type"] == "bill"
    assert evidence["bill_name"] == "Electric"
    assert evidence["days_until_due"] == 3


def test_gather_evidence_for_budget_overrun() -> None:
    recommendation = build_recommendation(
        RecommendationCategory.BUDGET,
        "Budget Overrun",
        "Your Food budget is over by $50.00.",
        "BudgetOverrunRule",
    )
    snapshot = build_snapshot()

    evidence = recommendation_explainer._gather_evidence(recommendation, snapshot)

    assert evidence["type"] == "budget"
    assert evidence["category"] == "Food"
    assert evidence["remaining"] == Decimal("-50.00")


def test_gather_evidence_for_budget_utilization() -> None:
    recommendation = build_recommendation(
        RecommendationCategory.BUDGET,
        "Budget Nearly Exhausted",
        "Your Food budget is 112% utilized.",
        "BudgetUtilizationRule",
    )
    snapshot = build_snapshot()

    evidence = recommendation_explainer._gather_evidence(recommendation, snapshot)

    assert evidence["type"] == "budget"
    assert evidence["category"] == "Food"
    assert evidence["utilization_percentage"] == pytest.approx(112.5)


def test_gather_evidence_for_expense_spike() -> None:
    recommendation = build_recommendation(
        RecommendationCategory.EXPENSES,
        "Expense Spike Detected",
        "Rent is significantly higher than your average expense.",
        "ExpenseSpikeRule",
    )
    snapshot = build_snapshot()

    evidence = recommendation_explainer._gather_evidence(recommendation, snapshot)

    assert evidence["type"] == "expense"
    assert evidence["expense_name"] == "Rent"
    assert evidence["average_expense"] == Decimal("300.00")


def test_gather_evidence_for_spending_concentration() -> None:
    recommendation = build_recommendation(
        RecommendationCategory.EXPENSES,
        "Spending Concentration Detected",
        "Housing represents 73% of your spending.",
        "SpendingConcentrationRule",
    )
    snapshot = build_snapshot()

    evidence = recommendation_explainer._gather_evidence(recommendation, snapshot)

    assert evidence["type"] == "expense_category_concentration"
    assert evidence["category"] == "Housing"
    assert evidence["concentration_percentage"] == pytest.approx(
        float(Decimal("1200.00") / Decimal("1650.00") * 100)
    )


def test_gather_evidence_falls_back_to_aggregate_for_aggregate_rules() -> None:
    """Aggregate-level rules have no single target entity to resolve."""
    recommendation = build_recommendation(
        RecommendationCategory.WEALTH,
        "Negative Net Worth",
        "Your net worth is negative.",
        "NetWorthRule",
    )
    snapshot = build_snapshot()

    evidence = recommendation_explainer._gather_evidence(recommendation, snapshot)

    assert evidence["type"] == "aggregate"
    assert evidence["net_worth"] == snapshot["net_worth"]
    assert evidence["health_score"] == snapshot["health_score"]


def test_gather_evidence_falls_back_when_entity_name_mismatch() -> None:
    """A resolved entity whose name isn't in the message should be discarded."""
    recommendation = build_debt_recommendation(
        message="Some other debt has a high interest rate.",
    )
    snapshot = build_snapshot()

    evidence = recommendation_explainer._gather_evidence(recommendation, snapshot)

    assert evidence["type"] == "aggregate"


def test_gather_evidence_falls_back_when_selector_finds_nothing() -> None:
    """A registered rule whose selector finds no matching entity falls back."""
    recommendation = build_recommendation(
        RecommendationCategory.BILLS,
        "Bill Due Soon",
        "Electric is due in 3 days.",
        "BillDueSoonRule",
    )
    snapshot = build_snapshot(bills=[])

    evidence = recommendation_explainer._gather_evidence(recommendation, snapshot)

    assert evidence["type"] == "aggregate"
