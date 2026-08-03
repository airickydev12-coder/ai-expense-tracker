from decimal import Decimal

from src.core.db import clear_test_database, initialize_database, set_test_database
from src.financial.bills.models import Bill
from src.financial.expenses.service import expenses
from src.financial.shared.categories import ExpenseCategory
from src.financial.users.repository import create_user
from src.financial.workflows.bill_payment import pay_bill


def test_pay_bill_creates_expense(tmp_path):
    # pay_bill's add_expense call has no db_path override, so it always
    # writes through the default DB_PATH. Redirect that default to an
    # isolated per-test database (same mechanism as
    # tests/conftest.py's _isolate_default_database) so this test neither
    # depends on nor mutates the real data/app.db, and so the user_id FK
    # on the expenses table has a real user row to reference.
    test_db_path = tmp_path / "test_app.db"
    initialize_database(test_db_path)
    set_test_database(test_db_path)
    try:
        user = create_user("alice", "alice@example.com", "hash", test_db_path)

        expenses.clear()

        bill = Bill(
            id=1,
            name="Electric",
            amount=Decimal("125.00"),
            due_day=15,
        )

        expense = pay_bill(user_id=user.id, bill=bill)

        assert bill.is_paid is True
        assert expense.name == "Electric"
        assert expense.amount == Decimal("125.00")
        assert expense.category == ExpenseCategory.UTILITIES
        assert len(expenses[user.id]) == 1
    finally:
        clear_test_database()
