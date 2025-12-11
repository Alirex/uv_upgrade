import typer

from uv_upx.cli.helpers.main import app as app_helpers
from uv_upx.cli.upgrade.main import app as app_upgrade

app = typer.Typer(
    pretty_exceptions_enable=False,
    pretty_exceptions_show_locals=False,
)

app.add_typer(app_upgrade, name="upgrade")
app.add_typer(app_helpers, name="helpers")
