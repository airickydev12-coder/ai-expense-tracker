HEALTH_SCORE_EXCELLENT_THRESHOLD = 85
HEALTH_SCORE_GOOD_THRESHOLD = 70
HEALTH_SCORE_FAIR_THRESHOLD = 50
HEALTH_SCORE_NEEDS_ATTENTION_THRESHOLD = 30


def get_health_status(score: int) -> str:
    """Return a health status label for a score."""
    if score >= HEALTH_SCORE_EXCELLENT_THRESHOLD:
        return "Excellent"

    if score >= HEALTH_SCORE_GOOD_THRESHOLD:
        return "Good"

    if score >= HEALTH_SCORE_FAIR_THRESHOLD:
        return "Fair"

    if score >= HEALTH_SCORE_NEEDS_ATTENTION_THRESHOLD:
        return "Needs Attention"

    return "Critical"
