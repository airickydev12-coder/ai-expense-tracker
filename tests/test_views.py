from src.presentation.views import show_menu


def test_show_menu_displays_budget_options(capsys):
    show_menu()

    captured = capsys.readouterr()

    assert "7. Manage Budgets" in captured.out
    assert "8. View Budget Report" in captured.out
    assert "9. Exit" in captured.out