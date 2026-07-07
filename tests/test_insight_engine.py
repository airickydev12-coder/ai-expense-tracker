from src.financial.insights.insight_engine import generate_insights


def test_generate_positive_insight():
    snapshot = {
        "net_cash_flow": 3000,
        "total_debt": 1000,
        "total_account_balance": 5000,
        "health_score": 85,
    }

    insights = generate_insights(snapshot)

    assert len(insights) == 1
    assert "Excellent financial health" in insights[0]


def test_generate_negative_insights():
    snapshot = {
        "net_cash_flow": -500,
        "total_debt": 10000,
        "total_account_balance": 1000,
        "health_score": 25,
    }

    insights = generate_insights(snapshot)

    assert len(insights) == 3