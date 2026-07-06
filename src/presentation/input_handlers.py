from src.financial.categories import ExpenseCategory
from src.presentation.views import display_categories


def select_category() -> ExpenseCategory | None:
    """
    Prompt the user to select an expense category.

    Returns:
        ExpenseCategory | None: Selected category, or None if invalid.
    """
    display_categories()
    choice = input("Choose a category number: ")

    try:
        index = int(choice) - 1
    except ValueError:
        print("Invalid category. Please enter a number.")
        return None

    categories = list(ExpenseCategory)

    if index < 0 or index >= len(categories):
        print("Invalid category number.")
        return None

    return categories[index]