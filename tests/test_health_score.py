from src.financial.engine.health_score import calculate_health_score


def test_calculate_strong_health_score():
    snapshot = {
        "net_cash_flow": 3000,
        "total_debt": 0,
        "total_account_balance": 5000,
        "total_goal_progress": 1000,
        "net_worth": 6000,
    }

    score = calculate_health_score(snapshot)

    assert score == 100


def test_calculate_weak_health_score():
    snapshot = {
        "net_cash_flow": -500,
        "total_debt": 5000,
        "total_account_balance": 1000,
        "total_goal_progress": 0,
        "net_worth": -4000,
    }

    score = calculate_health_score(snapshot)

    assert score == 5