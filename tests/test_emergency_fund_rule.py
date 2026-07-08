from src.financial.rules.emergency_fund_rule import EmergencyFundRule


def test_emergency_fund_rule_triggers():
    rule = EmergencyFundRule()

    snapshot = {
        "total_expenses": 2000,
        "total_account_balance": 3000,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert "less than 3 months" in result


def test_emergency_fund_rule_returns_none():
    rule = EmergencyFundRule()

    snapshot = {
        "total_expenses": 2000,
        "total_account_balance": 6000,
    }

    result = rule.evaluate(snapshot)

    assert result is None


def test_emergency_fund_rule_handles_zero_expenses():
    rule = EmergencyFundRule()

    snapshot = {
        "total_expenses": 0,
        "total_account_balance": 1000,
    }

    result = rule.evaluate(snapshot)

    assert result is None