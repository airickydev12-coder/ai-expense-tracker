from src.financial.recommendations.category import RecommendationCategory
from src.financial.recommendations.priority import RecommendationPriority
from src.financial.rules.bill_due_rule import BillDueSoonRule


def test_bill_due_soon_rule_triggers():
    rule = BillDueSoonRule()

    snapshot = {
        "current_day": 10,
        "bills": [
            {
                "name": "Electric",
                "due_day": 15,
                "is_paid": False,
            }
        ],
    }

    result = rule.evaluate(snapshot)

    assert result is not None
    assert result.priority == RecommendationPriority.HIGH
    assert result.category == RecommendationCategory.BILLS
    assert result.title == "Bill Due Soon"
    assert "Electric" in result.message


def test_bill_due_soon_rule_ignores_paid_bills():
    rule = BillDueSoonRule()

    snapshot = {
        "current_day": 10,
        "bills": [
            {
                "name": "Electric",
                "due_day": 15,
                "is_paid": True,
            }
        ],
    }

    result = rule.evaluate(snapshot)

    assert result is None


def test_bill_due_soon_rule_returns_none_when_not_due_soon():
    rule = BillDueSoonRule()

    snapshot = {
        "current_day": 10,
        "bills": [
            {
                "name": "Electric",
                "due_day": 25,
                "is_paid": False,
            }
        ],
    }

    result = rule.evaluate(snapshot)

    assert result is None
