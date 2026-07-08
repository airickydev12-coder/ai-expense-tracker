from src.financial.rules.debt_to_income_rule import DebtToIncomeRule


def test_debt_to_income_rule_triggers():
    rule = DebtToIncomeRule()

    snapshot = {
        "total_income": 5000,
        "total_debt": 3000,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert "debt is 60%" in result


def test_debt_to_income_rule_returns_none():
    rule = DebtToIncomeRule()

    snapshot = {
        "total_income": 5000,
        "total_debt": 1000,
    }

    result = rule.evaluate(snapshot)

    assert result is None


def test_debt_to_income_rule_handles_zero_income():
    rule = DebtToIncomeRule()

    snapshot = {
        "total_income": 0,
        "total_debt": 1000,
    }

    result = rule.evaluate(snapshot)

    assert result is None