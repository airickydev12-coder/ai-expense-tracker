from decimal import Decimal

from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.budget_overrun_rule import BudgetOverrunRule


def test_budget_overrun_rule_triggers():
    rule = BudgetOverrunRule()

    snapshot = {
        "budget_report": [
            {
                "category": "Food",
                "remaining": Decimal("-25.50"),
            }
        ]
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.CRITICAL
    assert result.category == RecommendationCategory.BUDGET
    assert result.title == "Budget Overrun"
    assert "Food" in result.message


def test_budget_overrun_rule_returns_none():
    rule = BudgetOverrunRule()

    snapshot = {
        "budget_report": [
            {
                "category": "Food",
                "remaining": Decimal("100.00"),
            }
        ]
    }

    result = rule.evaluate(snapshot)

    assert result is None
