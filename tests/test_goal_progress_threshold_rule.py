from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.goal_progress_threshold_rule import GoalProgressThresholdRule


def test_goal_progress_threshold_rule_triggers():
    rule = GoalProgressThresholdRule()

    snapshot = {
        "goals": [
            {
                "name": "Emergency Fund",
                "target_amount": 10000,
                "current_amount": 1000,
            }
        ]
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.MEDIUM
    assert result.category == RecommendationCategory.GOALS
    assert result.title == "Low Goal Progress"
    assert "Emergency Fund" in result.message


def test_goal_progress_threshold_rule_returns_none():
    rule = GoalProgressThresholdRule()

    snapshot = {
        "goals": [
            {
                "name": "Emergency Fund",
                "target_amount": 10000,
                "current_amount": 3000,
            }
        ]
    }

    result = rule.evaluate(snapshot)

    assert result is None