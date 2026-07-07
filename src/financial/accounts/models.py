from dataclasses import dataclass


@dataclass
class Account:
    """Represents a financial account."""

    id: int
    name: str
    account_type: str
    balance: float

    def __post_init__(self) -> None:
        """Validate the account after initialization."""
        if self.id <= 0:
            raise ValueError("Account ID must be greater than zero.")

        if not self.name.strip():
            raise ValueError("Account name cannot be empty.")

        if not self.account_type.strip():
            raise ValueError("Account type cannot be empty.")

    def to_dict(self) -> dict:
        """Convert the account to a dictionary for JSON storage."""
        return {
            "id": self.id,
            "name": self.name,
            "account_type": self.account_type,
            "balance": self.balance,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Account":
        """Create an Account from a dictionary."""
        return cls(
            id=int(data["id"]),
            name=data["name"],
            account_type=data["account_type"],
            balance=float(data["balance"]),
        )