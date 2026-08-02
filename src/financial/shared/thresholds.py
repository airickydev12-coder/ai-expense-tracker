"""
Business-rule threshold values shared between the recommendation engine
(src/financial/rules/) and the coach's deterministic insights
(src/financial/coach/insights.py), so the same financial condition is never
independently redefined by two different threshold literals.
"""

SAVINGS_RATE_LOW_THRESHOLD = 0.10
SAVINGS_RATE_STRONG_THRESHOLD = 0.20

EMERGENCY_FUND_TARGET_MONTHS_THRESHOLD = 3

DEBT_TO_INCOME_CRITICAL_THRESHOLD = 0.50

SPENDING_CONCENTRATION_THRESHOLD = 0.50
