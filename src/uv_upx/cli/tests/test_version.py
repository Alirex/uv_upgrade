import importlib.metadata
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from uv_upx.cli.main import app as app_full
from uv_upx.cli.upgrade.main import app as app_upgrade

if TYPE_CHECKING:
    import typer


@pytest.mark.parametrize("app", [app_full, app_upgrade])
def test_version(app: typer.Typer) -> None:
    result = CliRunner().invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output == f"uv-upx {importlib.metadata.version('uv-upx')}\n"
