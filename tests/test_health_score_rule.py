from src.financial.rules.health_score_rule import HealthScoreRule


def test_health_score_rule_triggers_for_low_score():
    rule = HealthScoreRule()

    snapshot = {
        "health_score": 35,
        "health_status": "Needs Attention",
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert "Needs Attention" in result


def test_health_score_rule_triggers_for_high_score():
    rule = HealthScoreRule()

    snapshot = {
        "health_score": 90,
        "health_status": "Excellent",
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert "Excellent" in result


def test_health_score_rule_returns_none_for_middle_score():
    rule = HealthScoreRule()

    snapshot = {
        "health_score": 70,
        "health_status": "Good",
    }

    result = rule.evaluate(snapshot)

    assert result is None