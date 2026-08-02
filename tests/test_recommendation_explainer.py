"""Tests for AI-generated debt-recommendation explanations."""

from decimal import Decimal

import anthropic
import httpx
import pytest

from src.core.exceptions import ExternalServiceError, NotFoundError, ValidationError
from src.financial.coach import recommendation_explainer
from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.models import Recommendation
from src.financial.recommendations.priority import RecommendationPriority


def build_debt_recommendation(
    source_rule: str = "HighInterestDebtRule",
    message: str = "Card A has a high interest rate of 27.40%.",
) -> Recommendation:
    return Recommendation(
        priority=RecommendationPriority.HIGH,
        category=RecommendationCategory.DEBT,
        title="High Interest Debt",
        message=message,
        action="Prioritize this debt for repayment.",
        source_rule=source_rule,
    )


def build_snapshot() -> dict:
    return {
        "total_income": Decimal("5000.00"),
        "total_debt": Decimal("4800.00"),
        "net_cash_flow": Decimal("300.00"),
        "total_account_balance": Decimal("2000.00"),
        "total_goal_progress": Decimal("500.00"),
        "debts": [
            {
                "id": 1,
                "name": "Card A",
                "balance": Decimal("4800.00"),
                "interest_rate": 27.4,
                "minimum_payment": Decimal("145.00"),
            }
        ],
    }


def test_explain_debt_recommendation_rejects_non_debt_category(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-DEBT recommendation should be rejected before any AI call."""
    recommendation = Recommendation(
        priority=RecommendationPriority.HIGH,
        category=RecommendationCategory.CASH_FLOW,
        title="Negative Cash Flow",
        message="Your expenses exceed your income.",
        action="Reduce spending or increase income.",
        source_rule="NegativeCashFlowRule",
    )

    monkeypatch.setattr(
        recommendation_explainer,
        "get_recommendation_by_key",
        lambda key: recommendation,
    )

    with pytest.raises(ValidationError):
        recommendation_explainer.explain_debt_recommendation("cash_flow:negative")


def test_explain_debt_recommendation_raises_not_found_for_unknown_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unknown recommendation key should raise NotFoundError."""
    monkeypatch.setattr(
        recommendation_explainer,
        "get_recommendation_by_key",
        lambda key: None,
    )

    with pytest.raises(NotFoundError):
        recommendation_explainer.explain_debt_recommendation("debt:unknown")


def test_explain_debt_recommendation_returns_structured_result(
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

    result = recommendation_explainer.explain_debt_recommendation(recommendation.key)

    assert result["recommendation_key"] == recommendation.key
    assert result["reason"] == "Card A has the highest APR."
    assert result["confidence"] == "High"
    assert result["evidence"]["type"] == "debt"
    assert result["evidence"]["debt_name"] == "Card A"
    assert result["evidence"]["payoff_months_saved"] is not None


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


def test_get_recommendation_evidence_rejects_non_debt_category(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-DEBT recommendation should be rejected."""
    recommendation = Recommendation(
        priority=RecommendationPriority.HIGH,
        category=RecommendationCategory.CASH_FLOW,
        title="Negative Cash Flow",
        message="Your expenses exceed your income.",
        action="Reduce spending or increase income.",
        source_rule="NegativeCashFlowRule",
    )

    monkeypatch.setattr(
        recommendation_explainer,
        "get_recommendation_by_key",
        lambda key: recommendation,
    )

    with pytest.raises(ValidationError):
        recommendation_explainer.get_recommendation_evidence("cash_flow:negative")


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


def test_resolve_target_debt_for_high_interest_rule() -> None:
    """The selector should mirror HighInterestDebtRule and match by name."""
    recommendation = build_debt_recommendation()
    snapshot = build_snapshot()

    debt = recommendation_explainer._resolve_target_debt(recommendation, snapshot)

    assert debt is not None
    assert debt["name"] == "Card A"


def test_resolve_target_debt_returns_none_for_aggregate_rules() -> None:
    """Aggregate-level rules have no single target debt to resolve."""
    recommendation = build_debt_recommendation(
        source_rule="DebtToIncomeRule",
        message="Your debt is 60% of your income.",
    )
    snapshot = build_snapshot()

    assert (
        recommendation_explainer._resolve_target_debt(recommendation, snapshot)
        is None
    )


def test_resolve_target_debt_falls_back_when_name_mismatch() -> None:
    """A resolved debt whose name isn't in the message should be discarded."""
    recommendation = build_debt_recommendation(
        message="Some other debt has a high interest rate.",
    )
    snapshot = build_snapshot()

    assert (
        recommendation_explainer._resolve_target_debt(recommendation, snapshot)
        is None
    )


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
