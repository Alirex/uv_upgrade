from uv_upx.cli.main import app as app_full
from uv_upx.cli.upgrade.main import app as app_upgrade
from uv_upx.logging_custom import init_logging


def main() -> None:
    init_logging()
    app_full()


def main_short() -> None:
    init_logging()
    app_upgrade()
