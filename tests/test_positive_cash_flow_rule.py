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
    assert "debt repayment" in result


def test_positive_cash_flow_with_no_goals_progress():
    rule = PositiveCashFlowAllocationRule()

    snapshot = {
        "net_cash_flow": 1000,
        "total_debt": 0,
        "total_goal_progress": 0,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert "financial goals" in result


def test_positive_cash_flow_general_recommendation():
    rule = PositiveCashFlowAllocationRule()

    snapshot = {
        "net_cash_flow": 1000,
        "total_debt": 0,
        "total_goal_progress": 500,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert "saving" in result


def test_positive_cash_flow_rule_returns_none():
    rule = PositiveCashFlowAllocationRule()

    snapshot = {
        "net_cash_flow": 0,
        "total_debt": 0,
        "total_goal_progress": 500,
    }

    result = rule.evaluate(snapshot)

    assert result is None