from src.core.logging import configure_logging
from src.financial.events.register import register_handlers
from src.presentation.cli import run_cli

if __name__ == "__main__":
    configure_logging()
    register_handlers()
    run_cli()
