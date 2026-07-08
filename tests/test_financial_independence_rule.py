from src.financial.rules.financial_independence_rule import (
    FinancialIndependenceRule,
)


def test_financial_independence_complete():
    rule = FinancialIndependenceRule()

    snapshot = {
        "net_worth": 900000,
        "total_expenses": 3000,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert "financial independence" in result


def test_financial_independence_progress():
    rule = FinancialIndependenceRule()

    snapshot = {
        "net_worth": 700000,
        "total_expenses": 3000,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert "way toward" in result


def test_financial_independence_returns_none():
    rule = FinancialIndependenceRule()

    snapshot = {
        "net_worth": 100000,
        "total_expenses": 3000,
    }

    result = rule.evaluate(snapshot)

    assert result is None