from typing import TYPE_CHECKING

from uv_upx.services.run_uv_related import run_uv_lock

if TYPE_CHECKING:
    import pathlib


def update_lock_file(
    project_root_path: pathlib.Path,
) -> None:
    # Because we want a fast update. Without triggering build for now.
    run_uv_lock(
        workdir=project_root_path,
        upgrade=True,
    )
