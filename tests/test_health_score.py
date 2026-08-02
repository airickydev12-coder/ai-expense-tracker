from src.financial.engine.health_score import (
    calculate_health_score,
    explain_health_score,
)


def test_explain_health_score_factors_sum_to_calculate_health_score():
    strong_snapshot = {
        "net_cash_flow": 3000,
        "total_debt": 0,
        "total_account_balance": 5000,
        "total_goal_progress": 1000,
        "net_worth": 6000,
    }

    weak_snapshot = {
        "net_cash_flow": -500,
        "total_debt": 5000,
        "total_account_balance": 1000,
        "total_goal_progress": 0,
        "net_worth": -4000,
    }

    for snapshot in (strong_snapshot, weak_snapshot):
        factors = explain_health_score(snapshot)
        total = sum(factor.points for factor in factors)

        assert max(0, min(100, total)) == calculate_health_score(snapshot)


def test_explain_health_score_returns_expected_factor_names():
    snapshot = {
        "net_cash_flow": 0,
        "total_debt": 100,
        "total_account_balance": 100,
        "total_goal_progress": 0,
        "net_worth": 0,
    }

    factors = explain_health_score(snapshot)

    assert [factor.name for factor in factors] == [
        "Baseline",
        "Cash Flow",
        "Debt Load",
        "Goal Progress",
        "Net Worth",
    ]


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
