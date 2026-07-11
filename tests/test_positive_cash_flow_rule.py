from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.positive_cash_flow_rule import (
    PositiveCashFlowAllocationRule,
)


def test_positive_cash_flow_with_debt():
    rule = PositiveCashFlowAllocationRule()

    snapshot = {
        "net_cash_flow": 1000,
        "total_debt": 5000,
        "total_goal_progress": 1000,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.HIGH
    assert result.category == RecommendationCategory.CASH_FLOW
    assert result.title == "Apply Cash Flow to Debt"


def test_positive_cash_flow_with_no_goal_progress():
    rule = PositiveCashFlowAllocationRule()

    snapshot = {
        "net_cash_flow": 1000,
        "total_debt": 0,
        "total_goal_progress": 0,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.MEDIUM
    assert result.category == RecommendationCategory.GOALS
    assert result.title == "Fund a Financial Goal"


def test_positive_cash_flow_general_recommendation():
    rule = PositiveCashFlowAllocationRule()

    snapshot = {
        "net_cash_flow": 1000,
        "total_debt": 0,
        "total_goal_progress": 500,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.LOW
    assert result.category == RecommendationCategory.WEALTH
    assert result.title == "Allocate Excess Cash Flow"


def test_positive_cash_flow_rule_returns_none():
    rule = PositiveCashFlowAllocationRule()

    snapshot = {
        "net_cash_flow": 0,
        "total_debt": 0,
        "total_goal_progress": 500,
    }

    assert rule.evaluate(snapshot) is None