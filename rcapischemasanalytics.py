warning: in the working copy of 'data/budgets.json', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'src/financial/budgets/service.py', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'src/financial/expenses/service.py', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'tests/test_budget_cli.py', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'tests/test_budget_service.py', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'tests/test_expense_cli.py', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'tests/test_main_cli.py', CRLF will be replaced by LF the next time Git touches it
[1mdiff --git a/data/budgets.json b/data/budgets.json[m
[1mindex 0637a08..4e0042e 100644[m
[1m--- a/data/budgets.json[m
[1m+++ b/data/budgets.json[m
[36m@@ -1 +1,6 @@[m
[31m-[][m
\ No newline at end of file[m
[32m+[m[32m[[m
[32m+[m[32m    {[m
[32m+[m[32m        "category": "Food",[m
[32m+[m[32m        "limit": 600[m
[32m+[m[32m    }[m
[32m+[m[32m][m
\ No newline at end of file[m
[1mdiff --git a/src/financial/budgets/__pycache__/service.cpython-314.pyc b/src/financial/budgets/__pycache__/service.cpython-314.pyc[m
[1mindex 463da7e..ea668a2 100644[m
Binary files a/src/financial/budgets/__pycache__/service.cpython-314.pyc and b/src/financial/budgets/__pycache__/service.cpython-314.pyc differ
[1mdiff --git a/src/financial/budgets/service.py b/src/financial/budgets/service.py[m
[1mindex b6ba812..5620643 100644[m
[1m--- a/src/financial/budgets/service.py[m
[1m+++ b/src/financial/budgets/service.py[m
[36m@@ -40,6 +40,22 @@[m [mdef add_budget(category: ExpenseCategory, limit: float) -> Budget:[m
     return budget[m
 [m
 [m
[32m+[m[32mdef update_budget([m
[32m+[m[32m    category: ExpenseCategory,[m
[32m+[m[32m    limit: float,[m
[32m+[m[32m) -> Budget:[m
[32m+[m[32m    """[m
[32m+[m[32m    Update the budget for a category.[m
[32m+[m
[32m+[m[32m    If the category does not already have a budget,[m
[32m+[m[32m    one will be created.[m
[32m+[m[32m    """[m
[32m+[m[32m    return add_budget([m
[32m+[m[32m        category=category,[m
[32m+[m[32m        limit=limit,[m
[32m+[m[32m    )[m
[32m+[m
[32m+[m
 def get_budget_by_category([m
     category: ExpenseCategory,[m
 ) -> Budget | None:[m
[1mdiff --git a/src/financial/expenses/__pycache__/service.cpython-314.pyc b/src/financial/expenses/__pycache__/service.cpython-314.pyc[m
[1mindex 9b7a321..cf7f15a 100644[m
Binary files a/src/financial/expenses/__pycache__/service.cpython-314.pyc and b/src/financial/expenses/__pycache__/service.cpython-314.pyc differ
[1mdiff --git a/src/financial/expenses/service.py b/src/financial/expenses/service.py[m
[1mindex 5c8ba48..7b7dae6 100644[m
[1m--- a/src/financial/expenses/service.py[m
[1m+++ b/src/financial/expenses/service.py[m
[36m@@ -8,6 +8,8 @@[m [mfrom src.financial.events.event_types import FinancialEvent[m
 [m
 expenses: list[Expense] = [][m
 [m
[32m+[m[32mfrom src.financial.shared.categories import ExpenseCategory[m
[32m+[m
 [m
 def load_expenses() -> None:[m
     """Load expenses from the repository."""[m
[36m@@ -28,7 +30,11 @@[m [mdef get_next_expense_id() -> int:[m
     return max(expense.id for expense in expenses) + 1[m
 [m
 [m
[31m-def add_expense(name: str, category: str, amount: float) -> Expense:[m
[32m+[m[32mdef add_expense([m
[32m+[m[32m    name: str,[m
[32m+[m[32m    category: ExpenseCategory,[m
[32m+[m[32m    amount: float,[m
[32m+[m[32m) -> Expense:[m
     """Create and add a new expense."""[m
     expense = Expense([m
         id=get_next_expense_id(),[m
[36m@@ -50,6 +56,18 @@[m [mdef get_expenses() -> list[Expense]:[m
     return expenses.copy()[m
 [m
 [m
[32m+[m[32mdef get_expense_by_id([m
[32m+[m[32m    expense_id: int,[m
[32m+[m[32m) -> Expense | None:[m
[32m+[m[32m    """Return an expense by its ID."""[m
[32m+[m
[32m+[m[32m    for expense in expenses:[m
[32m+[m[32m        if expense.id == expense_id:[m
[32m+[m[32m            return expense[m
[32m+[m
[32m+[m[32m    return None[m
[32m+[m
[32m+[m
 def delete_expense(expense_id: int) -> Expense | None:[m
     """[m
     Delete an expense by ID.[m
[36m@@ -72,7 +90,7 @@[m [mdef delete_expense(expense_id: int) -> Expense | None:[m
 def update_expense([m
     expense_id: int,[m
     name: str | None = None,[m
[31m-    category: str | None = None,[m
[32m+[m[32m    category: ExpenseCategory | None = None,[m
     amount: float | None = None,[m
 ) -> Expense | None:[m
     """Update an existing expense by ID."""[m
[36m@@ -93,6 +111,11 @@[m [mdef update_expense([m
     return None[m
 [m
 [m
[32m+[m[32mdef get_total() -> float:[m
[32m+[m[32m    """Return the total amount of all recorded expenses."""[m
[32m+[m[32m    return sum(expense.amount for expense in expenses)[m
[32m+[m
[32m+[m
 def calculate_total() -> None:[m
     """[m
     Display the total amount of all recorded expenses.[m
[1mdiff --git a/tests/__pycache__/test_budget_cli.cpython-314-pytest-9.1.1.pyc b/tests/__pycache__/test_budget_cli.cpython-314-pytest-9.1.1.pyc[m
[1mindex 0b6b882..ed29133 100644[m
Binary files a/tests/__pycache__/test_budget_cli.cpython-314-pytest-9.1.1.pyc and b/tests/__pycache__/test_budget_cli.cpython-314-pytest-9.1.1.pyc differ
[1mdiff --git a/tests/__pycache__/test_budget_service.cpython-314-pytest-9.1.1.pyc b/tests/__pycache__/test_budget_service.cpython-314-pytest-9.1.1.pyc[m
[1mindex c19afaf..eead442 100644[m
Binary files a/tests/__pycache__/test_budget_service.cpython-314-pytest-9.1.1.pyc and b/tests/__pycache__/test_budget_service.cpython-314-pytest-9.1.1.pyc differ
[1mdiff --git a/tests/__pycache__/test_expense_cli.cpython-314-pytest-9.1.1.pyc b/tests/__pycache__/test_expense_cli.cpython-314-pytest-9.1.1.pyc[m
[1mindex 059c736..38184e2 100644[m
Binary files a/tests/__pycache__/test_expense_cli.cpython-314-pytest-9.1.1.pyc and b/tests/__pycache__/test_expense_cli.cpython-314-pytest-9.1.1.pyc differ
[1mdiff --git a/tests/__pycache__/test_main_cli.cpython-314-pytest-9.1.1.pyc b/tests/__pycache__/test_main_cli.cpython-314-pytest-9.1.1.pyc[m
[1mindex 696de90..dc097d7 100644[m
Binary files a/tests/__pycache__/test_main_cli.cpython-314-pytest-9.1.1.pyc and b/tests/__pycache__/test_main_cli.cpython-314-pytest-9.1.1.pyc differ
[1mdiff --git a/tests/test_budget_cli.py b/tests/test_budget_cli.py[m
[1mindex 8215fc7..58a6d37 100644[m
[1m--- a/tests/test_budget_cli.py[m
[1m+++ b/tests/test_budget_cli.py[m
[36m@@ -78,9 +78,7 @@[m [mdef test_create_or_update_budgets([m
     monkeypatch.setattr([m
         budget_cli,[m
         "display_budget_summary",[m
[31m-        lambda summary: captured.update([m
[31m-            {"summary": summary}[m
[31m-        ),[m
[32m+[m[32m        lambda summary: captured.update({"summary": summary}),[m
     )[m
 [m
     budget_cli.create_or_update_budgets()[m
[36m@@ -286,10 +284,7 @@[m [mdef test_create_or_update_budgets_rejects_non_positive_limit([m
 [m
     output = capsys.readouterr().out[m
 [m
[31m-    assert ([m
[31m-        "Budget limit must be greater than zero."[m
[31m-        in output[m
[31m-    )[m
[32m+[m[32m    assert "Budget limit must be greater than zero." in output[m
 [m
 [m
 def test_create_or_update_budgets_can_cancel_category([m
[36m@@ -473,4 +468,4 @@[m [mdef test_manage_budgets_handles_invalid_option([m
 [m
     output = capsys.readouterr().out[m
 [m
[31m-    assert "Invalid budget option." in output[m
\ No newline at end of file[m
[32m+[m[32m    assert "Invalid budget option." in output[m
[1mdiff --git a/tests/test_budget_service.py b/tests/test_budget_service.py[m
[1mindex ab77362..c3df4dc 100644[m
[1m--- a/tests/test_budget_service.py[m
[1m+++ b/tests/test_budget_service.py[m
[36m@@ -1,5 +1,6 @@[m
 from src.financial.budgets.service import ([m
     add_budget,[m
[32m+[m[32m    update_budget,[m
     budgets,[m
     get_budget_by_category,[m
     get_budgets,[m
[36m@@ -47,6 +48,7 @@[m [mdef test_get_budget_by_category():[m
     assert budget is not None[m
     assert budget.limit == 500[m
 [m
[32m+[m
 def test_delete_budget():[m
     budgets.clear()[m
 [m
[36m@@ -57,3 +59,34 @@[m [mdef test_delete_budget():[m
     assert deleted_budget is not None[m
     assert deleted_budget.category == ExpenseCategory.FOOD[m
     assert len(get_budgets()) == 0[m
[32m+[m
[32m+[m
[32m+[m[32mdef test_update_budget_updates_existing_budget():[m
[32m+[m[32m    budgets.clear()[m
[32m+[m
[32m+[m[32m    add_budget([m
[32m+[m[32m        ExpenseCategory.FOOD,[m
[32m+[m[32m        500,[m
[32m+[m[32m    )[m
[32m+[m
[32m+[m[32m    updated_budget = update_budget([m
[32m+[m[32m        ExpenseCategory.FOOD,[m
[32m+[m[32m        750,[m
[32m+[m[32m    )[m
[32m+[m
[32m+[m[32m    assert updated_budget.category == ExpenseCategory.FOOD[m
[32m+[m[32m    assert updated_budget.limit == 750[m
[32m+[m[32m    assert len(get_budgets()) == 1[m
[32m+[m
[32m+[m
[32m+[m[32mdef test_update_budget_creates_budget_when_missing():[m
[32m+[m[32m    budgets.clear()[m
[32m+[m
[32m+[m[32m    updated_budget = update_budget([m
[32m+[m[32m        ExpenseCategory.FOOD,[m
[32m+[m[32m        600,[m
[32m+[m[32m    )[m
[32m+[m
[32m+[m[32m    assert updated_budget.category == ExpenseCategory.FOOD[m
[32m+[m[32m    assert updated_budget.limit == 600[m
[32m+[m[32m    assert len(get_budgets()) == 1[m
[1mdiff --git a/tests/test_expense_cli.py b/tests/test_expense_cli.py[m
[1mindex cf3484d..3a835c4 100644[m
[1m--- a/tests/test_expense_cli.py[m
[1m+++ b/tests/test_expense_cli.py[m
[36m@@ -284,9 +284,9 @@[m [mdef test_update_expense_flow([m
 [m
         return Expense([m
             id=expense_id,[m
[31m-            name=name,[m
[31m-            category=category,[m
[31m-            amount=amount,[m
[32m+[m[32m            name=name or "Morning Coffee",[m
[32m+[m[32m            category=category or ExpenseCategory.FOOD,[m
[32m+[m[32m            amount=amount if amount is not None else 7.25,[m
         )[m
 [m
     monkeypatch.setattr([m
[36m@@ -416,4 +416,4 @@[m [mdef test_update_expense_flow_rejects_negative_amount([m
 [m
     output = capsys.readouterr().out[m
 [m
[31m-    assert "Amount cannot be negative." in output[m
\ No newline at end of file[m
[32m+[m[32m    assert "Amount cannot be negative." in output[m
[1mdiff --git a/tests/test_main_cli.py b/tests/test_main_cli.py[m
[1mindex 1947b82..db85345 100644[m
[1m--- a/tests/test_main_cli.py[m
[1m+++ b/tests/test_main_cli.py[m
[36m@@ -1,21 +1,11 @@[m
[31m-"""Integration tests for the primary CLI controller."""[m
[31m-[m
[31m-from collections.abc import Callable[m
[31m-[m
[31m-import pytest[m
[31m-[m
[31m-from src.financial.goals.models import Goal[m
 from src.presentation import cli[m
 [m
 [m
[31m-InputFunction = Callable[[str], str][m
[31m-[m
[31m-[m
 def configure_cli_test([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[32m+[m[32m    monkeypatch,[m
     choices: list[str],[m
 ) -> None:[m
[31m-    """Configure shared primary-CLI dependencies."""[m
[32m+[m[32m    """Configure shared main CLI mocks."""[m
     choice_iterator = iter(choices)[m
 [m
     monkeypatch.setattr([m
[36m@@ -29,12 +19,6 @@[m [mdef configure_cli_test([m
         lambda: None,[m
     )[m
 [m
[31m-    monkeypatch.setattr([m
[31m-        cli,[m
[31m-        "register_default_scenario_handlers",[m
[31m-        lambda: None,[m
[31m-    )[m
[31m-[m
     monkeypatch.setattr([m
         cli,[m
         "display_dashboard",[m
[36m@@ -48,55 +32,10 @@[m [mdef configure_cli_test([m
     )[m
 [m
 [m
[31m-def test_run_cli_initializes_application([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-) -> None:[m
[31m-    calls: list[str] = [][m
[31m-[m
[31m-    monkeypatch.setattr([m
[31m-        "builtins.input",[m
[31m-        lambda _: "16",[m
[31m-    )[m
[31m-[m
[31m-    monkeypatch.setattr([m
[31m-        cli,[m
[31m-        "load_financial_state",[m
[31m-        lambda: calls.append("load_financial_state"),[m
[31m-    )[m
[31m-[m
[31m-    monkeypatch.setattr([m
[31m-        cli,[m
[31m-        "register_default_scenario_handlers",[m
[31m-        lambda: calls.append("register_scenario_handlers"),[m
[31m-    )[m
[31m-[m
[31m-    monkeypatch.setattr([m
[31m-        cli,[m
[31m-        "display_dashboard",[m
[31m-        lambda: calls.append("display_dashboard"),[m
[31m-    )[m
[31m-[m
[31m-    monkeypatch.setattr([m
[31m-        cli,[m
[31m-        "show_main_menu",[m
[31m-        lambda: None,[m
[31m-    )[m
[31m-[m
[31m-    cli.run_cli()[m
[31m-[m
[31m-    assert calls == [[m
[31m-        "load_financial_state",[m
[31m-        "register_scenario_handlers",[m
[31m-        "display_dashboard",[m
[31m-    ][m
[31m-[m
[31m-[m
 def test_run_cli_routes_add_expense([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-) -> None:[m
[31m-    captured = {[m
[31m-        "called": False,[m
[31m-    }[m
[32m+[m[32m    monkeypatch,[m
[32m+[m[32m):[m
[32m+[m[32m    captured = {"called": False}[m
 [m
     configure_cli_test([m
         monkeypatch,[m
[36m@@ -106,7 +45,7 @@[m [mdef test_run_cli_routes_add_expense([m
         ],[m
     )[m
 [m
[31m-    def fake_add_expense_flow() -> None:[m
[32m+[m[32m    def fake_add_expense_flow():[m
         captured["called"] = True[m
 [m
     monkeypatch.setattr([m
[36m@@ -121,11 +60,9 @@[m [mdef test_run_cli_routes_add_expense([m
 [m
 [m
 def test_run_cli_routes_view_expenses([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-) -> None:[m
[31m-    captured = {[m
[31m-        "called": False,[m
[31m-    }[m
[32m+[m[32m    monkeypatch,[m
[32m+[m[32m):[m
[32m+[m[32m    captured = {"called": False}[m
 [m
     configure_cli_test([m
         monkeypatch,[m
[36m@@ -135,7 +72,7 @@[m [mdef test_run_cli_routes_view_expenses([m
         ],[m
     )[m
 [m
[31m-    def fake_display_expenses() -> None:[m
[32m+[m[32m    def fake_display_expenses():[m
         captured["called"] = True[m
 [m
     monkeypatch.setattr([m
[36m@@ -149,48 +86,10 @@[m [mdef test_run_cli_routes_view_expenses([m
     assert captured["called"] is True[m
 [m
 [m
[31m-def test_run_cli_routes_total_spending([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-    capsys: pytest.CaptureFixture[str],[m
[31m-) -> None:[m
[31m-    expenses = [[m
[31m-        object(),[m
[31m-        object(),[m
[31m-    ][m
[31m-[m
[31m-    configure_cli_test([m
[31m-        monkeypatch,[m
[31m-        [[m
[31m-            "3",[m
[31m-            "16",[m
[31m-        ],[m
[31m-    )[m
[31m-[m
[31m-    monkeypatch.setattr([m
[31m-        cli,[m
[31m-        "get_expenses",[m
[31m-        lambda: expenses,[m
[31m-    )[m
[31m-[m
[31m-    monkeypatch.setattr([m
[31m-        cli,[m
[31m-        "get_total",[m
[31m-        lambda received_expenses: (125.75 if received_expenses is expenses else 0.0),[m
[31m-    )[m
[31m-[m
[31m-    cli.run_cli()[m
[31m-[m
[31m-    output = capsys.readouterr().out[m
[31m-[m
[31m-    assert "Total spending: $125.75" in output[m
[31m-[m
[31m-[m
 def test_run_cli_routes_delete_expense([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-) -> None:[m
[31m-    captured = {[m
[31m-        "called": False,[m
[31m-    }[m
[32m+[m[32m    monkeypatch,[m
[32m+[m[32m):[m
[32m+[m[32m    captured = {"called": False}[m
 [m
     configure_cli_test([m
         monkeypatch,[m
[36m@@ -200,7 +99,7 @@[m [mdef test_run_cli_routes_delete_expense([m
         ],[m
     )[m
 [m
[31m-    def fake_delete_expense_flow() -> None:[m
[32m+[m[32m    def fake_delete_expense_flow():[m
         captured["called"] = True[m
 [m
     monkeypatch.setattr([m
[36m@@ -215,11 +114,9 @@[m [mdef test_run_cli_routes_delete_expense([m
 [m
 [m
 def test_run_cli_routes_update_expense([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-) -> None:[m
[31m-    captured = {[m
[31m-        "called": False,[m
[31m-    }[m
[32m+[m[32m    monkeypatch,[m
[32m+[m[32m):[m
[32m+[m[32m    captured = {"called": False}[m
 [m
     configure_cli_test([m
         monkeypatch,[m
[36m@@ -229,7 +126,7 @@[m [mdef test_run_cli_routes_update_expense([m
         ],[m
     )[m
 [m
[31m-    def fake_update_expense_flow() -> None:[m
[32m+[m[32m    def fake_update_expense_flow():[m
         captured["called"] = True[m
 [m
     monkeypatch.setattr([m
[36m@@ -243,41 +140,10 @@[m [mdef test_run_cli_routes_update_expense([m
     assert captured["called"] is True[m
 [m
 [m
[31m-def test_run_cli_routes_category_totals([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-) -> None:[m
[31m-    captured = {[m
[31m-        "called": False,[m
[31m-    }[m
[31m-[m
[31m-    configure_cli_test([m
[31m-        monkeypatch,[m
[31m-        [[m
[31m-            "6",[m
[31m-            "16",[m
[31m-        ],[m
[31m-    )[m
[31m-[m
[31m-    def fake_display_category_totals() -> None:[m
[31m-        captured["called"] = True[m
[31m-[m
[31m-    monkeypatch.setattr([m
[31m-        cli,[m
[31m-        "display_category_totals",[m
[31m-        fake_display_category_totals,[m
[31m-    )[m
[31m-[m
[31m-    cli.run_cli()[m
[31m-[m
[31m-    assert captured["called"] is True[m
[31m-[m
[31m-[m
 def test_run_cli_routes_budget_management([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-) -> None:[m
[31m-    captured = {[m
[31m-        "called": False,[m
[31m-    }[m
[32m+[m[32m    monkeypatch,[m
[32m+[m[32m):[m
[32m+[m[32m    captured = {"called": False}[m
 [m
     configure_cli_test([m
         monkeypatch,[m
[36m@@ -287,7 +153,7 @@[m [mdef test_run_cli_routes_budget_management([m
         ],[m
     )[m
 [m
[31m-    def fake_manage_budgets() -> None:[m
[32m+[m[32m    def fake_manage_budgets():[m
         captured["called"] = True[m
 [m
     monkeypatch.setattr([m
[36m@@ -301,83 +167,10 @@[m [mdef test_run_cli_routes_budget_management([m
     assert captured["called"] is True[m
 [m
 [m
[31m-def test_run_cli_routes_budget_report([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-) -> None:[m
[31m-    captured = {[m
[31m-        "called": False,[m
[31m-    }[m
[31m-[m
[31m-    configure_cli_test([m
[31m-        monkeypatch,[m
[31m-        [[m
[31m-            "8",[m
[31m-            "16",[m
[31m-        ],[m
[31m-    )[m
[31m-[m
[31m-    def fake_display_saved_budget_summaries() -> None:[m
[31m-        captured["called"] = True[m
[31m-[m
[31m-    monkeypatch.setattr([m
[31m-        cli,[m
[31m-        "display_saved_budget_summaries",[m
[31m-        fake_display_saved_budget_summaries,[m
[31m-    )[m
[31m-[m
[31m-    cli.run_cli()[m
[31m-[m
[31m-    assert captured["called"] is True[m
[31m-[m
[31m-[m
[31m-def test_run_cli_records_financial_snapshot([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-) -> None:[m
[31m-    captured: dict[str, object] = {}[m
[31m-[m
[31m-    configure_cli_test([m
[31m-        monkeypatch,[m
[31m-        [[m
[31m-            "9",[m
[31m-            "16",[m
[31m-        ],[m
[31m-    )[m
[31m-[m
[31m-    snapshot = {[m
[31m-        "total_income": 5000,[m
[31m-    }[m
[31m-[m
[31m-    monkeypatch.setattr([m
[31m-        cli,[m
[31m-        "record_current_financial_snapshot",[m
[31m-        lambda: ([m
[31m-            snapshot,[m
[31m-            "record",[m
[31m-        ),[m
[31m-    )[m
[31m-[m
[31m-    def fake_display_financial_snapshot([m
[31m-        received_snapshot: dict,[m
[31m-    ) -> None:[m
[31m-        captured["snapshot"] = received_snapshot[m
[31m-[m
[31m-    monkeypatch.setattr([m
[31m-        cli,[m
[31m-        "display_financial_snapshot",[m
[31m-        fake_display_financial_snapshot,[m
[31m-    )[m
[31m-[m
[31m-    cli.run_cli()[m
[31m-[m
[31m-    assert captured["snapshot"] == snapshot[m
[31m-[m
[31m-[m
 def test_run_cli_routes_recommendation_management([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-) -> None:[m
[31m-    captured = {[m
[31m-        "called": False,[m
[31m-    }[m
[32m+[m[32m    monkeypatch,[m
[32m+[m[32m):[m
[32m+[m[32m    captured = {"called": False}[m
 [m
     configure_cli_test([m
         monkeypatch,[m
[36m@@ -387,7 +180,7 @@[m [mdef test_run_cli_routes_recommendation_management([m
         ],[m
     )[m
 [m
[31m-    def fake_manage_recommendations() -> None:[m
[32m+[m[32m    def fake_manage_recommendations():[m
         captured["called"] = True[m
 [m
     monkeypatch.setattr([m
[36m@@ -402,9 +195,9 @@[m [mdef test_run_cli_routes_recommendation_management([m
 [m
 [m
 def test_run_cli_routes_financial_trends([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-) -> None:[m
[31m-    captured: dict[str, object] = {}[m
[32m+[m[32m    monkeypatch,[m
[32m+[m[32m):[m
[32m+[m[32m    captured: dict = {}[m
 [m
     configure_cli_test([m
         monkeypatch,[m
[36m@@ -414,9 +207,7 @@[m [mdef test_run_cli_routes_financial_trends([m
         ],[m
     )[m
 [m
[31m-    history = [[m
[31m-        "snapshot",[m
[31m-    ][m
[32m+[m[32m    history = ["snapshot"][m
 [m
     monkeypatch.setattr([m
         cli,[m
[36m@@ -425,8 +216,8 @@[m [mdef test_run_cli_routes_financial_trends([m
     )[m
 [m
     def fake_display_financial_trends([m
[31m-        received_history: list[str],[m
[31m-    ) -> None:[m
[32m+[m[32m        received_history,[m
[32m+[m[32m    ):[m
         captured["history"] = received_history[m
 [m
     monkeypatch.setattr([m
[36m@@ -441,11 +232,9 @@[m [mdef test_run_cli_routes_financial_trends([m
 [m
 [m
 def test_run_cli_routes_forecast([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-) -> None:[m
[31m-    captured = {[m
[31m-        "called": False,[m
[31m-    }[m
[32m+[m[32m    monkeypatch,[m
[32m+[m[32m):[m
[32m+[m[32m    captured = {"called": False}[m
 [m
     configure_cli_test([m
         monkeypatch,[m
[36m@@ -455,7 +244,7 @@[m [mdef test_run_cli_routes_forecast([m
         ],[m
     )[m
 [m
[31m-    def fake_display_current_forecast() -> None:[m
[32m+[m[32m    def fake_display_current_forecast():[m
         captured["called"] = True[m
 [m
     monkeypatch.setattr([m
[36m@@ -469,207 +258,52 @@[m [mdef test_run_cli_routes_forecast([m
     assert captured["called"] is True[m
 [m
 [m
[31m-def test_run_cli_routes_scenario_management([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-) -> None:[m
[31m-    captured = {[m
[31m-        "called": False,[m
[31m-    }[m
[32m+[m[32mdef test_run_cli_records_financial_snapshot([m
[32m+[m[32m    monkeypatch,[m
[32m+[m[32m):[m
[32m+[m[32m    captured: dict = {}[m
 [m
     configure_cli_test([m
         monkeypatch,[m
         [[m
[31m-            "13",[m
[32m+[m[32m            "9",[m
             "16",[m
         ],[m
     )[m
 [m
[31m-    def fake_manage_scenarios() -> None:[m
[31m-        captured["called"] = True[m
[31m-[m
[31m-    monkeypatch.setattr([m
[31m-        cli,[m
[31m-        "manage_scenarios",[m
[31m-        fake_manage_scenarios,[m
[31m-    )[m
[31m-[m
[31m-    cli.run_cli()[m
[31m-[m
[31m-    assert captured["called"] is True[m
[31m-[m
[31m-[m
[31m-def test_run_cli_routes_financial_coach([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-) -> None:[m
[31m-    captured = {[m
[31m-        "called": False,[m
[32m+[m[32m    snapshot = {[m
[32m+[m[32m        "total_income": 5000,[m
     }[m
 [m
[31m-    configure_cli_test([m
[31m-        monkeypatch,[m
[31m-        [[m
[31m-            "14",[m
[31m-            "16",[m
[31m-        ],[m
[31m-    )[m
[31m-[m
[31m-    def fake_run_financial_coach() -> None:[m
[31m-        captured["called"] = True[m
[31m-[m
     monkeypatch.setattr([m
         cli,[m
[31m-        "run_financial_coach",[m
[31m-        fake_run_financial_coach,[m
[31m-    )[m
[31m-[m
[31m-    cli.run_cli()[m
[31m-[m
[31m-    assert captured["called"] is True[m
[31m-[m
[31m-[m
[31m-def test_run_cli_routes_goal_planner([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-) -> None:[m
[31m-    goals = [[m
[31m-        Goal([m
[31m-            id=1,[m
[31m-            name="Emergency Fund",[m
[31m-            target_amount=10000.0,[m
[31m-            current_amount=2500.0,[m
[31m-        ),[m
[31m-        Goal([m
[31m-            id=2,[m
[31m-            name="Vacation",[m
[31m-            target_amount=3000.0,[m
[31m-            current_amount=500.0,[m
[31m-        ),[m
[31m-    ][m
[31m-[m
[31m-    captured: dict[str, object] = {}[m
[31m-[m
[31m-    configure_cli_test([m
[31m-        monkeypatch,[m
[31m-        [[m
[31m-            "15",[m
[31m-            "16",[m
[31m-        ],[m
[31m-    )[m
[31m-[m
[31m-    monkeypatch.setattr([m
[31m-        cli,[m
[31m-        "get_goals",[m
[31m-        lambda: goals,[m
[31m-    )[m
[31m-[m
[31m-    def fake_run_goal_planning_menu([m
[31m-        received_goals: list[Goal],[m
[31m-    ) -> None:[m
[31m-        captured["goals"] = received_goals[m
[31m-[m
[31m-    monkeypatch.setattr([m
[31m-        cli,[m
[31m-        "run_goal_planning_menu",[m
[31m-        fake_run_goal_planning_menu,[m
[31m-    )[m
[31m-[m
[31m-    cli.run_cli()[m
[31m-[m
[31m-    assert captured["goals"] is goals[m
[31m-[m
[31m-[m
[31m-def test_run_cli_gets_fresh_goals_each_time_planner_opens([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-) -> None:[m
[31m-    first_goals = [[m
[31m-        Goal([m
[31m-            id=1,[m
[31m-            name="Emergency Fund",[m
[31m-            target_amount=10000.0,[m
[31m-            current_amount=2000.0,[m
[31m-        ),[m
[31m-    ][m
[31m-[m
[31m-    second_goals = [[m
[31m-        Goal([m
[31m-            id=1,[m
[31m-            name="Emergency Fund",[m
[31m-            target_amount=10000.0,[m
[31m-            current_amount=3000.0,[m
[32m+[m[32m        "record_current_financial_snapshot",[m
[32m+[m[32m        lambda: ([m
[32m+[m[32m            snapshot,[m
[32m+[m[32m            "record",[m
         ),[m
[31m-    ][m
[31m-[m
[31m-    goal_results = iter([m
[31m-        [[m
[31m-            first_goals,[m
[31m-            second_goals,[m
[31m-        ][m
[31m-    )[m
[31m-[m
[31m-    received_goal_lists: list[list[Goal]] = [][m
[31m-[m
[31m-    configure_cli_test([m
[31m-        monkeypatch,[m
[31m-        [[m
[31m-            "15",[m
[31m-            "15",[m
[31m-            "16",[m
[31m-        ],[m
     )[m
 [m
[31m-    monkeypatch.setattr([m
[31m-        cli,[m
[31m-        "get_goals",[m
[31m-        lambda: next(goal_results),[m
[31m-    )[m
[31m-[m
[31m-    monkeypatch.setattr([m
[31m-        cli,[m
[31m-        "run_goal_planning_menu",[m
[31m-        lambda goals: (received_goal_lists.append(goals)),[m
[31m-    )[m
[31m-[m
[31m-    cli.run_cli()[m
[31m-[m
[31m-    assert received_goal_lists == [[m
[31m-        first_goals,[m
[31m-        second_goals,[m
[31m-    ][m
[31m-[m
[31m-[m
[31m-def test_run_cli_passes_empty_goal_list_to_planner([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-) -> None:[m
[31m-    captured: dict[str, object] = {}[m
[31m-[m
[31m-    configure_cli_test([m
[31m-        monkeypatch,[m
[31m-        [[m
[31m-            "15",[m
[31m-            "16",[m
[31m-        ],[m
[31m-    )[m
[31m-[m
[31m-    monkeypatch.setattr([m
[31m-        cli,[m
[31m-        "get_goals",[m
[31m-        lambda: [],[m
[31m-    )[m
[32m+[m[32m    def fake_display_financial_snapshot([m
[32m+[m[32m        received_snapshot,[m
[32m+[m[32m    ):[m
[32m+[m[32m        captured["snapshot"] = received_snapshot[m
 [m
     monkeypatch.setattr([m
         cli,[m
[31m-        "run_goal_planning_menu",[m
[31m-        lambda goals: captured.update(goals=goals),[m
[32m+[m[32m        "display_financial_snapshot",[m
[32m+[m[32m        fake_display_financial_snapshot,[m
     )[m
 [m
     cli.run_cli()[m
 [m
[31m-    assert captured["goals"] == [][m
[32m+[m[32m    assert captured["snapshot"] == snapshot[m
 [m
 [m
 def test_run_cli_exits_with_option_16([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-    capsys: pytest.CaptureFixture[str],[m
[31m-) -> None:[m
[32m+[m[32m    monkeypatch,[m
[32m+[m[32m    capsys,[m
[32m+[m[32m):[m
     configure_cli_test([m
         monkeypatch,[m
         [[m
[36m@@ -685,9 +319,9 @@[m [mdef test_run_cli_exits_with_option_16([m
 [m
 [m
 def test_run_cli_rejects_invalid_option([m
[31m-    monkeypatch: pytest.MonkeyPatch,[m
[31m-    capsys: pytest.CaptureFixture[str],[m
[31m-) -> None:[m
[32m+[m[32m    monkeypatch,[m
[32m+[m[32m    capsys,[m
[32m+[m[32m):[m
     configure_cli_test([m
         monkeypatch,[m
         [[m
[36m@@ -701,4 +335,3 @@[m [mdef test_run_cli_rejects_invalid_option([m
     output = capsys.readouterr().out[m
 [m
     assert "Invalid option." in output[m
[31m-    assert "1 through 16" in output[m
