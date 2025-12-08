import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathlib


def run_uv_lock(workdir: pathlib.Path) -> None:
    subprocess.run(
        ["uv", "lock"],  # noqa: S607
        check=True,
        cwd=workdir,
    )
