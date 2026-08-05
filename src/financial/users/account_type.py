from enum import Enum


class AccountType(str, Enum):
    """What kind of account this is (ADULT/MINOR) -- orthogonal to
    PlatformRole (see role.py), which answers what this user can operate on
    the platform, not what kind of product-domain account they have. See
    ADR-007."""

    ADULT = "adult"
    MINOR = "minor"
