"""CSV export for the AI-generated monthly financial review."""

import csv
import io

from src.core.exceptions import BusinessRuleError

CSV_HEADER = ["section", "field", "value"]


def export_monthly_review_to_csv(review: dict) -> str:
    """
    Return a monthly review serialized as CSV text.

    Only a review with status "ok" (see monthly_review.py) has real content
    to export -- raises BusinessRuleError for the degraded "no_history" /
    "insufficient_recent_history" shapes, since there is nothing meaningful
    to flatten into rows yet.
    """
    if review["status"] != "ok":
        raise BusinessRuleError(
            "No monthly review is available to export yet: "
            f"{review.get('message', review['status'])}"
        )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADER)

    writer.writerow(["Overview", "period_start", review["period_start"]])
    writer.writerow(["Overview", "period_end", review["period_end"]])
    writer.writerow(["Overview", "overall_summary", review["overall_summary"]])

    income_vs_expenses = review["income_vs_expenses"]
    writer.writerow(["Income vs Expenses", "narrative", income_vs_expenses["narrative"]])
    writer.writerow(
        ["Income vs Expenses", "income_change", str(income_vs_expenses["income_change"])]
    )
    writer.writerow(
        ["Income vs Expenses", "expense_change", str(income_vs_expenses["expense_change"])]
    )

    cash_flow = review["cash_flow"]
    writer.writerow(["Cash Flow", "narrative", cash_flow["narrative"]])
    writer.writerow(["Cash Flow", "change", str(cash_flow["change"])])
    writer.writerow(["Cash Flow", "direction", cash_flow["direction"]])

    debt_progress = review["debt_progress"]
    writer.writerow(["Debt Progress", "narrative", debt_progress["narrative"]])
    writer.writerow(["Debt Progress", "total_debt", str(debt_progress["total_debt"])])

    writer.writerow(["Savings Progress", "narrative", review["savings_progress"]["narrative"]])
    writer.writerow(["Goal Status", "narrative", review["goal_status"]["narrative"]])

    health_score = review["health_score"]
    writer.writerow(["Health Score", "narrative", health_score["narrative"]])
    writer.writerow(["Health Score", "change", str(health_score["change"])])
    writer.writerow(["Health Score", "direction", health_score["direction"]])
    writer.writerow(["Health Score", "current_score", str(health_score["current_score"])])

    for action in review["top_actions"]:
        writer.writerow(
            [
                "Top Action",
                f"{action['priority']}: {action['title']}",
                action["message"],
            ]
        )

    for trend in review["category_trends"]:
        writer.writerow(
            [
                "Category Trend",
                trend["category"],
                f"{trend['direction']} ({trend['change']})",
            ]
        )

    for gap in review["known_gaps"]:
        writer.writerow(["Known Gap", "", gap])

    return buffer.getvalue()
