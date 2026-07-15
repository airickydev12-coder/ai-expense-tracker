from src.financial.application.financial_state import (
    build_current_financial_snapshot,
)
from src.financial.recommendations.history import (
    RecommendationRecord,
)
from src.financial.recommendations.history_service import (
    activate_recommendation,
    complete_recommendation,
    dismiss_recommendation,
    get_recommendation_history,
    suppress_recommendation,
)
from src.presentation.views import (
    display_recommendation_history,
    display_recommendation_management_menu,
    display_recommendations,
)


def select_recommendation_key(
    recommendations: list[dict],
) -> str | None:
    """Select a recommendation from the active list."""
    if not recommendations:
        print("No active recommendations are available.")
        return None

    display_recommendations(recommendations)

    selection_text = input(
        "Enter the recommendation number: "
    ).strip()

    try:
        selection = int(selection_text)
    except ValueError:
        print("Invalid selection. Please enter a number.")
        return None

    if selection < 1 or selection > len(recommendations):
        print("Recommendation selection is out of range.")
        return None

    recommendation_key = recommendations[
        selection - 1
    ].get("key")

    if not recommendation_key:
        print("The selected recommendation has no key.")
        return None

    return str(recommendation_key)


def select_history_record_key(
    records: list[RecommendationRecord],
) -> str | None:
    """Select a recommendation from lifecycle history."""
    if not records:
        print("No recommendation history is available.")
        return None

    sorted_records = sorted(
        records,
        key=lambda record: record.updated_at,
        reverse=True,
    )

    display_recommendation_history(sorted_records)

    selection_text = input(
        "Enter the history record number: "
    ).strip()

    try:
        selection = int(selection_text)
    except ValueError:
        print("Invalid selection. Please enter a number.")
        return None

    if selection < 1 or selection > len(sorted_records):
        print("History selection is out of range.")
        return None

    return sorted_records[
        selection - 1
    ].recommendation_key


def manage_recommendations() -> None:
    """Run the recommendation-management submenu."""
    while True:
        display_recommendation_management_menu()

        recommendation_choice = input(
            "Choose an option: "
        ).strip()

        snapshot = build_current_financial_snapshot()
        active_recommendations = snapshot.get(
            "recommendations",
            [],
        )
        history = get_recommendation_history()

        if recommendation_choice == "1":
            display_recommendations(
                active_recommendations
            )

        elif recommendation_choice == "2":
            display_recommendation_history(history)

        elif recommendation_choice == "3":
            recommendation_key = (
                select_history_record_key(history)
            )

            if recommendation_key is None:
                continue

            note = input("Optional note: ").strip()

            record = activate_recommendation(
                recommendation_key,
                note=note,
            )

            if record is None:
                print("Recommendation record not found.")
            else:
                print(
                    "Recommendation marked as active."
                )

        elif recommendation_choice == "4":
            recommendation_key = (
                select_recommendation_key(
                    active_recommendations
                )
            )

            if recommendation_key is None:
                continue

            note = input(
                "Optional completion note: "
            ).strip()

            record = complete_recommendation(
                recommendation_key,
                note=note,
            )

            if record is None:
                print("Recommendation record not found.")
            else:
                print(
                    "Recommendation marked as completed."
                )

        elif recommendation_choice == "5":
            recommendation_key = (
                select_recommendation_key(
                    active_recommendations
                )
            )

            if recommendation_key is None:
                continue

            note = input(
                "Optional dismissal note: "
            ).strip()

            record = dismiss_recommendation(
                recommendation_key,
                note=note,
            )

            if record is None:
                print("Recommendation record not found.")
            else:
                print("Recommendation dismissed.")

        elif recommendation_choice == "6":
            recommendation_key = (
                select_recommendation_key(
                    active_recommendations
                )
            )

            if recommendation_key is None:
                continue

            note = input(
                "Optional suppression note: "
            ).strip()

            record = suppress_recommendation(
                recommendation_key,
                note=note,
            )

            if record is None:
                print("Recommendation record not found.")
            else:
                print("Recommendation suppressed.")

        elif recommendation_choice == "7":
            return

        else:
            print(
                "Invalid recommendation option. "
                "Please choose 1 through 7."
            )