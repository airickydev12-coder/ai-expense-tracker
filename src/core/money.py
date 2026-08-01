"""
Shared money utilities for the Financial Core application.

All financial calculations should use these helpers instead of
calling Decimal() or round() directly.

Using one module guarantees:

- Consistent rounding
- Accurate financial arithmetic
- Centralized currency formatting
- Easier future changes
"""

from __future__ import annotations

from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_HALF_UP,
)

from src.core.exceptions import ValidationError


# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------

CURRENCY_PRECISION = Decimal("0.01")

ZERO = Decimal("0.00")


# ----------------------------------------------------------------------
# Conversion
# ----------------------------------------------------------------------


def to_money(value: object) -> Decimal:
    """
    Convert a supported value into a Decimal.

    Supported types:

    - Decimal
    - int
    - float
    - str

    Returns a Decimal rounded to two places.
    """
    if isinstance(value, Decimal):
        amount = value

    elif isinstance(value, int):
        amount = Decimal(value)

    elif isinstance(value, float):
        # Never pass floats directly into Decimal().
        amount = Decimal(str(value))

    elif isinstance(value, str):
        try:
            amount = Decimal(value.strip())
        except InvalidOperation as error:
            raise ValidationError(f"Invalid monetary value: {value!r}") from error

    else:
        raise TypeError(f"Unsupported monetary value: {type(value)}")

    return quantize_money(amount)


# ----------------------------------------------------------------------
# Formatting
# ----------------------------------------------------------------------


def format_money(value: object) -> str:
    """
    Return a formatted currency string.

    Example:

        Decimal("1234.5")

    becomes

        "$1,234.50"
    """
    amount = to_money(value)

    return f"${amount:,.2f}"


# ----------------------------------------------------------------------
# Rounding
# ----------------------------------------------------------------------


def quantize_money(value: Decimal) -> Decimal:
    """
    Round to two decimal places.

    Uses ROUND_HALF_UP which is the standard
    for most financial software.
    """
    return value.quantize(
        CURRENCY_PRECISION,
        rounding=ROUND_HALF_UP,
    )


# ----------------------------------------------------------------------
# Arithmetic
# ----------------------------------------------------------------------


def add_money(
    left: object,
    right: object,
) -> Decimal:
    """Add two monetary values."""
    return quantize_money(to_money(left) + to_money(right))


def subtract_money(
    left: object,
    right: object,
) -> Decimal:
    """Subtract two monetary values."""
    return quantize_money(to_money(left) - to_money(right))


def multiply_money(
    amount: object,
    multiplier: object,
) -> Decimal:
    """
    Multiply a monetary amount.

    Used for percentages, taxes,
    projections, etc.
    """
    result = to_money(amount) * Decimal(str(multiplier))

    return quantize_money(result)


def divide_money(
    amount: object,
    divisor: object,
) -> Decimal:
    """
    Divide a monetary amount.

    Raises ZeroDivisionError if divisor is zero.
    """
    divisor_decimal = Decimal(str(divisor))

    result = to_money(amount) / divisor_decimal

    return quantize_money(result)


# ----------------------------------------------------------------------
# Comparison
# ----------------------------------------------------------------------


def is_zero(value: object) -> bool:
    """Return True if value equals zero."""
    return to_money(value) == ZERO


def is_positive(value: object) -> bool:
    """Return True if value is greater than zero."""
    return to_money(value) > ZERO


def is_negative(value: object) -> bool:
    """Return True if value is less than zero."""
    return to_money(value) < ZERO


# ----------------------------------------------------------------------
# Serialization
# ----------------------------------------------------------------------


def money_to_json(value: Decimal) -> str:
    """
    Convert Decimal to a JSON-safe string.

    Example:

        Decimal("123.45")

    becomes

        "123.45"
    """
    return format(
        quantize_money(value),
        "f",
    )


def money_from_json(value: str) -> Decimal:
    """
    Convert JSON string back into Decimal.
    """
    return to_money(value)
