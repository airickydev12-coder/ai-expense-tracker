from src.financial.scenarios.factory import (
    register_default_scenario_handlers,
)
from src.financial.scenarios.models import (
    ScenarioType,
)
from src.financial.scenarios.service import (
    reset_scenario_handlers,
    scenario_service,
)


def setup_function():
    """Reset handlers before each test."""
    reset_scenario_handlers()


def teardown_function():
    """Reset handlers after each test."""
    reset_scenario_handlers()


def test_register_default_scenario_handlers():
    register_default_scenario_handlers()

    assert scenario_service.has_handler(ScenarioType.EXPENSE_REDUCTION)
    assert scenario_service.has_handler(ScenarioType.INCOME_INCREASE)
    assert scenario_service.has_handler(ScenarioType.ADDITIONAL_SAVINGS)
    assert scenario_service.has_handler(ScenarioType.EXTRA_DEBT_PAYMENT)

    assert len(scenario_service.get_registered_types()) == 4


def test_register_default_handlers_is_repeatable():
    register_default_scenario_handlers()
    register_default_scenario_handlers()

    assert len(scenario_service.get_registered_types()) == 4
