def get_health_status(score: int) -> str:
    """Return a health status label for a score."""
    if score >= 85:
        return "Excellent"

    if score >= 70:
        return "Good"

    if score >= 50:
        return "Fair"

    if score >= 30:
        return "Needs Attention"

    return "Critical"