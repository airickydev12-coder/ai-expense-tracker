from decimal import Decimal

from src.financial.expenses.models import Expense
from src.financial.shared.categories import ExpenseCategory
from src.presentation import expense_cli


def build_expense() -> Expense:
    """Create an expense for CLI tests."""
    return Expense(
        id=1,
        name="Coffee",
        category=ExpenseCategory.FOOD,
        amount=Decimal("5.50"),
    )


def test_add_expense_flow(
    monkeypatch,
    capsys,
):
    captured: dict = {}

    inputs = iter(
        [
            "Coffee",
            "5.50",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    monkeypatch.setattr(
        expense_cli,
        "get_cli_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        expense_cli,
        "select_category",
        lambda: ExpenseCategory.FOOD,
    )

    def fake_add_expense(
        user_id,
        name,
        category,
        amount,
    ):
        captured["name"] = name
        captured["category"] = category
        captured["amount"] = amount
        return build_expense()

    monkeypatch.setattr(
        expense_cli,
        "add_expense",
        fake_add_expense,
    )

    expense_cli.add_expense_flow()

    output = capsys.readouterr().out

    assert captured["name"] == "Coffee"
    assert captured["category"] == ExpenseCategory.FOOD
    assert captured["amount"] == Decimal("5.50")
    assert "Expense added successfully!" in output


def test_add_expense_flow_returns_when_category_cancelled(
    monkeypatch,
):
    captured = {"called": False}

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "Coffee",
    )

    monkeypatch.setattr(
        expense_cli,
        "select_category",
        lambda: None,
    )

    def fake_add_expense(*args, **kwargs):
        captured["called"] = True

    monkeypatch.setattr(
        expense_cli,
        "add_expense",
        fake_add_expense,
    )

    expense_cli.add_expense_flow()

    assert captured["called"] is False


def test_add_expense_flow_rejects_invalid_amount(
    monkeypatch,
    capsys,
):
    inputs = iter(
        [
            "Coffee",
            "invalid",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    monkeypatch.setattr(
        expense_cli,
        "select_category",
        lambda: ExpenseCategory.FOOD,
    )

    expense_cli.add_expense_flow()

    output = capsys.readouterr().out

    assert "Invalid amount" in output


def test_add_expense_flow_rejects_negative_amount(
    monkeypatch,
    capsys,
):
    inputs = iter(
        [
            "Coffee",
            "-5",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    monkeypatch.setattr(
        expense_cli,
        "select_category",
        lambda: ExpenseCategory.FOOD,
    )

    expense_cli.add_expense_flow()

    output = capsys.readouterr().out

    assert "Amount cannot be negative." in output


def test_delete_expense_flow(
    monkeypatch,
    capsys,
):
    captured: dict = {}
    expense = build_expense()

    monkeypatch.setattr(
        expense_cli,
        "get_cli_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        expense_cli,
        "display_expenses",
        lambda: None,
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "1",
    )

    def fake_delete_expense(
        user_id: int,
        expense_id: int,
    ):
        captured["expense_id"] = expense_id
        return expense

    monkeypatch.setattr(
        expense_cli,
        "delete_expense",
        fake_delete_expense,
    )

    expense_cli.delete_expense_flow()

    output = capsys.readouterr().out

    assert captured["expense_id"] == 1
    assert "Deleted expense: Coffee" in output


def test_delete_expense_flow_rejects_invalid_id(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        expense_cli,
        "display_expenses",
        lambda: None,
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "invalid",
    )

    expense_cli.delete_expense_flow()

    output = capsys.readouterr().out

    assert "Invalid input" in output


def test_delete_expense_flow_handles_missing_expense(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        expense_cli,
        "get_cli_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        expense_cli,
        "display_expenses",
        lambda: None,
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "999",
    )

    monkeypatch.setattr(
        expense_cli,
        "delete_expense",
        lambda user_id, expense_id: None,
    )

    expense_cli.delete_expense_flow()

    output = capsys.readouterr().out

    assert "Expense not found." in output


def test_update_expense_flow(
    monkeypatch,
    capsys,
):
    captured: dict = {}

    inputs = iter(
        [
            "1",
            "Morning Coffee",
            "y",
            "7.25",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    monkeypatch.setattr(
        expense_cli,
        "get_cli_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        expense_cli,
        "display_expenses",
        lambda: None,
    )

    monkeypatch.setattr(
        expense_cli,
        "select_category",
        lambda: ExpenseCategory.FOOD,
    )

    def fake_update_expense(
        user_id,
        expense_id,
        name=None,
        category=None,
        amount=None,
    ):
        captured["expense_id"] = expense_id
        captured["name"] = name
        captured["category"] = category
        captured["amount"] = amount

        return Expense(
            id=expense_id,
            name=name or "Morning Coffee",
            category=category or ExpenseCategory.FOOD,
            amount=amount if amount is not None else Decimal("7.25"),
        )

    monkeypatch.setattr(
        expense_cli,
        "update_expense",
        fake_update_expense,
    )

    expense_cli.update_expense_flow()

    output = capsys.readouterr().out

    assert captured["expense_id"] == 1
    assert captured["name"] == "Morning Coffee"
    assert captured["category"] == ExpenseCategory.FOOD
    assert captured["amount"] == Decimal("7.25")
    assert "Updated expense: Morning Coffee" in output


def test_update_expense_flow_preserves_blank_fields(
    monkeypatch,
):
    captured: dict = {}

    inputs = iter(
        [
            "1",
            "",
            "n",
            "",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    monkeypatch.setattr(
        expense_cli,
        "get_cli_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        expense_cli,
        "display_expenses",
        lambda: None,
    )

    def fake_update_expense(
        user_id,
        expense_id,
        name=None,
        category=None,
        amount=None,
    ):
        captured["expense_id"] = expense_id
        captured["name"] = name
        captured["category"] = category
        captured["amount"] = amount
        return build_expense()

    monkeypatch.setattr(
        expense_cli,
        "update_expense",
        fake_update_expense,
    )

    expense_cli.update_expense_flow()

    assert captured["expense_id"] == 1
    assert captured["name"] is None
    assert captured["category"] is None
    assert captured["amount"] is None


def test_update_expense_flow_rejects_invalid_amount(
    monkeypatch,
    capsys,
):
    inputs = iter(
        [
            "1",
            "",
            "n",
            "invalid",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    monkeypatch.setattr(
        expense_cli,
        "display_expenses",
        lambda: None,
    )

    expense_cli.update_expense_flow()

    output = capsys.readouterr().out

    assert "Invalid amount" in output


def test_update_expense_flow_rejects_negative_amount(
    monkeypatch,
    capsys,
):
    inputs = iter(
        [
            "1",
            "",
            "n",
            "-10",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    monkeypatch.setattr(
        expense_cli,
        "display_expenses",
        lambda: None,
    )

    expense_cli.update_expense_flow()

    output = capsys.readouterr().out

    assert "Amount cannot be negative." in output
