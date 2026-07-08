from src.financial.rules.budget_overrun_rule import BudgetOverrunRule


def test_budget_overrun_rule_triggers():
    rule = BudgetOverrunRule()

    snapshot = {
        "budget_report": [
            {
                "category": "Food",
                "remaining": -25.50,
            }
        ]
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert "Food budget is over" in result


def test_budget_overrun_rule_returns_none():
    rule = BudgetOverrunRule()

    snapshot = {
        "budget_report": [
            {
                "category": "Food",
                "remaining": 100,
            }
        ]
    }

    result = rule.evaluate(snapshot)

    assert result is None