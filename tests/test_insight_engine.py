from decimal import Decimal

from src.financial.insights.insight_engine import generate_insights


def test_generate_positive_insight():
    snapshot = {
        "net_cash_flow": Decimal("3000.00"),
        "total_debt": Decimal("1000.00"),
        "total_account_balance": Decimal("5000.00"),
        "health_score": 85,
    }

    insights = generate_insights(snapshot)

    assert len(insights) == 1
    assert "Excellent financial health" in insights[0]


def test_generate_negative_insights():
    snapshot = {
        "net_cash_flow": Decimal("-500.00"),
        "total_debt": Decimal("10000.00"),
        "total_account_balance": Decimal("1000.00"),
        "health_score": 25,
    }

    insights = generate_insights(snapshot)

    assert len(insights) == 3
