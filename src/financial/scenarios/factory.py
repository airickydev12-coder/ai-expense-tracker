from src.financial.scenarios.debt_scenario import (
    register_extra_debt_payment_scenario,
)
from src.financial.scenarios.expense_scenario import (
    register_expense_reduction_scenario,
)
from src.financial.scenarios.income_scenario import (
    register_income_increase_scenario,
)
from src.financial.scenarios.savings_scenario import (
    register_additional_savings_scenario,
)
from src.financial.scenarios.service import (
    reset_scenario_handlers,
)


def register_default_scenario_handlers() -> None:
    """Register all built-in financial scenario handlers."""
    reset_scenario_handlers()

    register_expense_reduction_scenario()
    register_income_increase_scenario()
    register_additional_savings_scenario()
    register_extra_debt_payment_scenario()
