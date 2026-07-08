from src.financial.rules.debt_rule import DebtRatioRule


def test_debt_rule_triggers():
    rule = DebtRatioRule()

    snapshot = {
        "total_debt": 6000,
        "total_account_balance": 3000,
    }

    result = rule.evaluate(snapshot)

    assert result is not None


def test_debt_rule_handles_zero_balance():
    rule = DebtRatioRule()

    snapshot = {
        "total_debt": 1000,
        "total_account_balance": 0,
    }

    result = rule.evaluate(snapshot)

    assert result is not None


def test_debt_rule_returns_none():
    rule = DebtRatioRule()

    snapshot = {
        "total_debt": 1000,
        "total_account_balance": 5000,
    }

    assert rule.evaluate(snapshot) is None