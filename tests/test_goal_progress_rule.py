from src.financial.rules.goal_progress_rule import GoalProgressRule


def test_goal_progress_rule_triggers():
    rule = GoalProgressRule()

    snapshot = {
        "total_goal_progress": 0,
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert "financial goals" in result


def test_goal_progress_rule_returns_none():
    rule = GoalProgressRule()

    snapshot = {
        "total_goal_progress": 1000,
    }

    result = rule.evaluate(snapshot)

    assert result is None