import subprocess
from typing import TYPE_CHECKING

from uv_upx.services.run_uv_related.exceptions import UnresolvedDependencyError

if TYPE_CHECKING:
    import pathlib


def run_uv_lock(
    workdir: pathlib.Path,
    *,
    upgrade: bool = False,
) -> None:
    # uv lock --upgrade
    command = ["uv", "lock"]
    if upgrade:
        command.append("--upgrade")
    try:
        subprocess.run(  # noqa: S603
            # uv lock --upgrade
            command,
            check=True,
            cwd=workdir,
        )
    except subprocess.CalledProcessError as e:
        msg = "Failed to resolve dependencies with 'uv lock'. Please check your dependency specifications."
        raise UnresolvedDependencyError(
            msg,
        ) from e
