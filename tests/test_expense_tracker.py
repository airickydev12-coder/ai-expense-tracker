from src.expense_tracker import expenses, get_total


def test_get_total():
    expenses.clear()

    expenses.append({
        "name": "Coffee",
        "category": "Food",
        "amount": 5.25,
    })

    expenses.append({
        "name": "Tea",
        "category": "Food",
        "amount": 4.00,
    })

    total = get_total()

    assert total == 9.25