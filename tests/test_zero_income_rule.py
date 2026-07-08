from src.financial.rules.zero_income_rule import ZeroIncomeRule


def test_zero_income_rule_triggers():
    rule = ZeroIncomeRule()

    snapshot = {
        "total_income": 0,
        "total_expenses": 1500,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert "No income has been recorded" in result


def test_zero_income_rule_returns_none_when_income_exists():
    rule = ZeroIncomeRule()

    snapshot = {
        "total_income": 5000,
        "total_expenses": 1500,
    }

    result = rule.evaluate(snapshot)

    assert result is None


def test_zero_income_rule_returns_none_when_no_expenses():
    rule = ZeroIncomeRule()

    snapshot = {
        "total_income": 0,
        "total_expenses": 0,
    }

    result = rule.evaluate(snapshot)

    assert result is None