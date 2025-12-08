import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathlib


class UnresolvedDependencyError(Exception):
    pass


def run_uv_lock(workdir: pathlib.Path) -> None:
    try:
        subprocess.run(
            ["uv", "lock"],  # noqa: S607
            check=True,
            cwd=workdir,
        )
    except subprocess.CalledProcessError as e:
        msg = "Failed to resolve dependencies with 'uv lock'. Please check your dependency specifications."
        raise UnresolvedDependencyError(
            msg,
        ) from e
