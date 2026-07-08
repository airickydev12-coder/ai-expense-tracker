from src.financial.rules.cash_flow_rule import NegativeCashFlowRule


def test_negative_cash_flow_rule_returns_recommendation():
    rule = NegativeCashFlowRule()

    snapshot = {
        "net_cash_flow": -100,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == "Critical"
    assert result.category == "Cash Flow"
    assert result.title == "Negative Cash Flow"


def test_negative_cash_flow_rule_returns_none():
    rule = NegativeCashFlowRule()

    snapshot = {
        "net_cash_flow": 100,
    }

    result = rule.evaluate(snapshot)

    assert result is None