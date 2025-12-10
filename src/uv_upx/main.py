from uv_upx.cli.main import app
from uv_upx.logging_custom import init_logging


def main() -> None:
    init_logging()
    app()
