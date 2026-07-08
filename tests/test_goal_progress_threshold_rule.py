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
    assert "less than 25% funded" in result


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