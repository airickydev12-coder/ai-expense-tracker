from src.financial.budgets.models import Budget
from src.financial.shared.categories import ExpenseCategory
from src.presentation import budget_cli


def build_budget(
    category: ExpenseCategory = ExpenseCategory.FOOD,
    limit: float = 500,
) -> Budget:
    """Create a budget for CLI tests."""
    return Budget(
        category=category,
        limit=limit,
    )


def build_summary() -> dict:
    """Create a budget summary for CLI tests."""
    return {
        "category": "Food",
        "limit": 500,
        "spent": 100,
        "remaining": 400,
        "status": "Within Budget",
    }


def test_create_or_update_budgets(
    monkeypatch,
    capsys,
):
    captured: dict = {}

    inputs = iter(
        [
            "500",
            "n",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    monkeypatch.setattr(
        budget_cli,
        "select_category",
        lambda: ExpenseCategory.FOOD,
    )

    def fake_add_budget(
        category,
        limit,
    ):
        captured["category"] = category
        captured["limit"] = limit
        return build_budget(category, limit)

    monkeypatch.setattr(
        budget_cli,
        "add_budget",
        fake_add_budget,
    )

    monkeypatch.setattr(
        budget_cli,
        "get_expenses",
        lambda: [],
    )

    monkeypatch.setattr(
        budget_cli,
        "get_budget_summary",
        lambda budget, expenses: build_summary(),
    )

    monkeypatch.setattr(
        budget_cli,
        "display_budget_summary",
        lambda summary: captured.update({"summary": summary}),
    )

    budget_cli.create_or_update_budgets()

    output = capsys.readouterr().out

    assert captured["category"] == ExpenseCategory.FOOD
    assert captured["limit"] == 500
    assert captured["summary"]["remaining"] == 400
    assert "Budget saved successfully." in output


def test_create_or_update_multiple_budgets(
    monkeypatch,
):
    captured: list[tuple[ExpenseCategory, float]] = []

    categories = iter(
        [
            ExpenseCategory.FOOD,
            ExpenseCategory.HOUSING,
        ]
    )

    inputs = iter(
        [
            "500",
            "y",
            "1500",
            "n",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    monkeypatch.setattr(
        budget_cli,
        "select_category",
        lambda: next(categories),
    )

    def fake_add_budget(
        category,
        limit,
    ):
        captured.append(
            (
                category,
                limit,
            )
        )
        return build_budget(category, limit)

    monkeypatch.setattr(
        budget_cli,
        "add_budget",
        fake_add_budget,
    )

    monkeypatch.setattr(
        budget_cli,
        "get_expenses",
        lambda: [],
    )

    monkeypatch.setattr(
        budget_cli,
        "get_budget_summary",
        lambda budget, expenses: build_summary(),
    )

    monkeypatch.setattr(
        budget_cli,
        "display_budget_summary",
        lambda summary: None,
    )

    budget_cli.create_or_update_budgets()

    assert captured == [
        (
            ExpenseCategory.FOOD,
            500,
        ),
        (
            ExpenseCategory.HOUSING,
            1500,
        ),
    ]


def test_create_or_update_budgets_rejects_invalid_limit(
    monkeypatch,
    capsys,
):
    inputs = iter(
        [
            "invalid",
            "500",
            "n",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    monkeypatch.setattr(
        budget_cli,
        "select_category",
        lambda: ExpenseCategory.FOOD,
    )

    monkeypatch.setattr(
        budget_cli,
        "add_budget",
        lambda category, limit: build_budget(
            category,
            limit,
        ),
    )

    monkeypatch.setattr(
        budget_cli,
        "get_expenses",
        lambda: [],
    )

    monkeypatch.setattr(
        budget_cli,
        "get_budget_summary",
        lambda budget, expenses: build_summary(),
    )

    monkeypatch.setattr(
        budget_cli,
        "display_budget_summary",
        lambda summary: None,
    )

    budget_cli.create_or_update_budgets()

    output = capsys.readouterr().out

    assert "Invalid budget limit" in output


def test_create_or_update_budgets_rejects_non_positive_limit(
    monkeypatch,
    capsys,
):
    inputs = iter(
        [
            "0",
            "500",
            "n",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    monkeypatch.setattr(
        budget_cli,
        "select_category",
        lambda: ExpenseCategory.FOOD,
    )

    monkeypatch.setattr(
        budget_cli,
        "add_budget",
        lambda category, limit: build_budget(
            category,
            limit,
        ),
    )

    monkeypatch.setattr(
        budget_cli,
        "get_expenses",
        lambda: [],
    )

    monkeypatch.setattr(
        budget_cli,
        "get_budget_summary",
        lambda budget, expenses: build_summary(),
    )

    monkeypatch.setattr(
        budget_cli,
        "display_budget_summary",
        lambda summary: None,
    )

    budget_cli.create_or_update_budgets()

    output = capsys.readouterr().out

    assert "Budget limit must be greater than zero." in output


def test_create_or_update_budgets_can_cancel_category(
    monkeypatch,
):
    inputs = iter(
        [
            "n",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    monkeypatch.setattr(
        budget_cli,
        "select_category",
        lambda: None,
    )

    budget_cli.create_or_update_budgets()


def test_delete_budget_flow(
    monkeypatch,
    capsys,
):
    captured: dict = {}
    budget = build_budget()

    monkeypatch.setattr(
        budget_cli,
        "select_category",
        lambda: ExpenseCategory.FOOD,
    )

    def fake_delete_budget(category):
        captured["category"] = category
        return budget

    monkeypatch.setattr(
        budget_cli,
        "delete_budget",
        fake_delete_budget,
    )

    budget_cli.delete_budget_flow()

    output = capsys.readouterr().out

    assert captured["category"] == ExpenseCategory.FOOD
    assert "Deleted budget for Food." in output


def test_delete_budget_flow_handles_missing_budget(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        budget_cli,
        "select_category",
        lambda: ExpenseCategory.FOOD,
    )

    monkeypatch.setattr(
        budget_cli,
        "delete_budget",
        lambda category: None,
    )

    budget_cli.delete_budget_flow()

    output = capsys.readouterr().out

    assert "Budget not found." in output


def test_delete_budget_flow_returns_when_cancelled(
    monkeypatch,
):
    captured = {"called": False}

    monkeypatch.setattr(
        budget_cli,
        "select_category",
        lambda: None,
    )

    def fake_delete_budget(category):
        captured["called"] = True

    monkeypatch.setattr(
        budget_cli,
        "delete_budget",
        fake_delete_budget,
    )

    budget_cli.delete_budget_flow()

    assert captured["called"] is False


def test_manage_budgets_routes_create(
    monkeypatch,
):
    captured = {"called": False}

    monkeypatch.setattr(
        budget_cli,
        "display_current_budgets",
        lambda: None,
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "1",
    )

    def fake_create():
        captured["called"] = True

    monkeypatch.setattr(
        budget_cli,
        "create_or_update_budgets",
        fake_create,
    )

    budget_cli.manage_budgets()

    assert captured["called"] is True


def test_manage_budgets_routes_delete(
    monkeypatch,
):
    captured = {"called": False}

    monkeypatch.setattr(
        budget_cli,
        "display_current_budgets",
        lambda: None,
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "2",
    )

    def fake_delete():
        captured["called"] = True

    monkeypatch.setattr(
        budget_cli,
        "delete_budget_flow",
        fake_delete,
    )

    budget_cli.manage_budgets()

    assert captured["called"] is True


def test_manage_budgets_handles_invalid_option(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        budget_cli,
        "display_current_budgets",
        lambda: None,
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "invalid",
    )

    budget_cli.manage_budgets()

    output = capsys.readouterr().out

    assert "Invalid budget option." in output
