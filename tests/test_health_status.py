from src.financial.engine.health_status import get_health_status


def test_excellent_health_status():
    assert get_health_status(90) == "Excellent"


def test_good_health_status():
    assert get_health_status(75) == "Good"


def test_fair_health_status():
    assert get_health_status(55) == "Fair"


def test_needs_attention_health_status():
    assert get_health_status(35) == "Needs Attention"


def test_critical_health_status():
    assert get_health_status(20) == "Critical"