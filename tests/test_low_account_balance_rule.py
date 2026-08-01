from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.low_account_balance_rule import LowAccountBalanceRule

from decimal import Decimal


def test_low_account_balance_rule_triggers():
    rule = LowAccountBalanceRule()

    snapshot = {
        "total_account_balance": Decimal("500.00"),
        "total_expenses": Decimal("2000.00"),
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.HIGH
    assert result.category == RecommendationCategory.SAVINGS
    assert result.title == "Low Cash Reserves"


def test_low_account_balance_rule_returns_none():
    rule = LowAccountBalanceRule()

    snapshot = {
        "total_account_balance": Decimal("3000.00"),
        "total_expenses": Decimal("2000.00"),
    }

    result = rule.evaluate(snapshot)

    assert result is None
