"""
Shared, domain-agnostic constants for the Financial Core application.

These are cross-cutting values with no natural home in a single
financial domain package. Domain-specific business-rule thresholds
belong next to the rule that uses them, not here.
"""

from __future__ import annotations

MONTHS_PER_YEAR = 12

SECONDS_PER_DAY = 86400

STANDARD_FORECAST_HORIZONS_DAYS = (30, 90, 365)
