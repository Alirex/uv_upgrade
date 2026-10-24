from typing import Annotated

import typer

from uv_upx.cli.helpers.main import app as app_helpers
from uv_upx.cli.upgrade.main import app as app_upgrade
from uv_upx.cli.upgrade.main import version_callback

app = typer.Typer(
    pretty_exceptions_enable=False,
    pretty_exceptions_show_locals=False,
)

app.add_typer(app_upgrade, name="upgrade")
app.add_typer(app_helpers, name="helpers")


@app.callback()
def main(
    *,
    version: Annotated[  # pyright: ignore[reportUnusedParameter]
        bool | None,
        typer.Option(
            "--version",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """Upgrade dependencies in uv projects."""
