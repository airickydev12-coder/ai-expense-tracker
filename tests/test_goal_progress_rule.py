from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.goal_progress_rule import GoalProgressRule


def test_goal_progress_rule_triggers():
    rule = GoalProgressRule()

    snapshot = {
        "total_goal_progress": 0,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.MEDIUM
    assert result.category == RecommendationCategory.GOALS
    assert result.title == "No Goal Progress"


def test_goal_progress_rule_returns_none():
    rule = GoalProgressRule()

    snapshot = {
        "total_goal_progress": 1000,
    }

    result = rule.evaluate(snapshot)

    assert result is None