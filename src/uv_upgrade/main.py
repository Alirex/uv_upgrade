from uv_upgrade.cli.main import app
from uv_upgrade.logging_custom import init_logging


def main() -> None:
    init_logging()
    app()
