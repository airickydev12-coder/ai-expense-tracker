from src.financial.rules.goal_completion_rule import GoalCompletionRule


def test_goal_completion_rule_triggers():
    rule = GoalCompletionRule()

    snapshot = {
        "goals": [
            {
                "name": "Emergency Fund",
                "target_amount": 10000,
                "current_amount": 10000,
            }
        ]
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert "fully funded" in result


def test_goal_completion_rule_returns_none():
    rule = GoalCompletionRule()

    snapshot = {
        "goals": [
            {
                "name": "Emergency Fund",
                "target_amount": 10000,
                "current_amount": 2500,
            }
        ]
    }

    result = rule.evaluate(snapshot)

    assert result is None