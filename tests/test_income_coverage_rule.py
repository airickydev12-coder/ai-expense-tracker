from src.financial.rules.income_coverage_rule import IncomeCoverageRule


def test_income_coverage_rule_triggers():
    rule = IncomeCoverageRule()

    snapshot = {
        "total_income": 1500,
        "total_expenses": 2000,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert "income does not fully cover" in result


def test_income_coverage_rule_returns_none():
    rule = IncomeCoverageRule()

    snapshot = {
        "total_income": 3000,
        "total_expenses": 2000,
    }

    result = rule.evaluate(snapshot)

    assert result is None