from src.financial.rules.budget_rule import BudgetUtilizationRule


def test_budget_rule_triggers():
    rule = BudgetUtilizationRule()

    snapshot = {
        "budget_report": [
            {
                "category": "Food",
                "limit": 500,
                "spent": 475,
            }
        ]
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == "High"
    assert result.category == "Budget"
    assert result.title == "Budget Nearly Exhausted"
    assert "Food" in result.message


def test_budget_rule_returns_none():
    rule = BudgetUtilizationRule()

    snapshot = {
        "budget_report": [
            {
                "category": "Food",
                "limit": 500,
                "spent": 100,
            }
        ]
    }

    assert rule.evaluate(snapshot) is None