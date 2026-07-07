def calculate_health_score(snapshot: dict) -> int:
    """
    Calculate a basic financial health score from a financial snapshot.

    Score range:
        0 to 100
    """
    score = 50

    if snapshot["net_cash_flow"] > 0:
        score += 20
    elif snapshot["net_cash_flow"] < 0:
        score -= 20

    if snapshot["total_debt"] == 0:
        score += 15
    elif snapshot["total_debt"] > snapshot["total_account_balance"]:
        score -= 15

    if snapshot["total_goal_progress"] > 0:
        score += 10

    if snapshot["net_worth"] > 0:
        score += 5
    elif snapshot["net_worth"] < 0:
        score -= 10

    return max(0, min(100, score))