from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.debt_rule import DebtRatioRule


def test_debt_rule_triggers():
    rule = DebtRatioRule()

    snapshot = {
        "total_debt": 5000,
        "total_account_balance": 4000,
        "total_goal_progress": 1000,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.HIGH
    assert result.category == RecommendationCategory.DEBT
    assert result.title == "High Debt Ratio"


def test_debt_rule_returns_none():
    rule = DebtRatioRule()

    snapshot = {
        "total_debt": 1000,
        "total_account_balance": 9000,
        "total_goal_progress": 2000,
    }

    assert rule.evaluate(snapshot) is None