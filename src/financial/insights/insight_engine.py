def generate_insights(snapshot: dict) -> list[str]:
    """
    Generate actionable financial insights from a financial snapshot.
    """
    insights = []

    if snapshot["net_cash_flow"] < 0:
        insights.append(
            "Your expenses exceed your income. Reduce spending or increase income."
        )

    if snapshot["total_debt"] > snapshot["total_account_balance"]:
        insights.append(
            "Your debt exceeds your available cash. "
            "Consider prioritizing debt repayment."
        )

    if snapshot["health_score"] >= 85:
        insights.append(
            "Excellent financial health. Continue building wealth and investing."
        )

    if snapshot["health_score"] < 50:
        insights.append(
            "Your financial health needs attention. Review your budget and debt."
        )

    if not insights:
        insights.append("Your finances are stable. Keep monitoring your progress.")

    return insights
