from logging_custom.init_logging import init_logging
from uv_upgrade.cli.main import app


def main() -> None:
    init_logging()
    app()
