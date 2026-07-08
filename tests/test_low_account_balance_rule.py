from src.financial.rules.low_account_balance_rule import LowAccountBalanceRule


def test_low_account_balance_rule_triggers():
    rule = LowAccountBalanceRule()

    snapshot = {
        "total_account_balance": 500,
        "total_expenses": 2000,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert "less than one month" in result


def test_low_account_balance_rule_returns_none():
    rule = LowAccountBalanceRule()

    snapshot = {
        "total_account_balance": 3000,
        "total_expenses": 2000,
    }

    result = rule.evaluate(snapshot)

    assert result is None