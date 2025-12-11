from typing import TYPE_CHECKING

from uv_upx.services.run_uv_related import UvSyncMode, run_uv_lock, run_uv_sync

if TYPE_CHECKING:
    import pathlib


def update_lock_file(
    project_root_path: pathlib.Path,
    *,
    no_sync: bool = False,
) -> None:
    if no_sync:
        # Because we want a fast update. Without triggering build for now.
        run_uv_lock(
            workdir=project_root_path,
            upgrade=True,
        )
    else:
        # Because we want to check build problems also.
        run_uv_sync(
            workdir=project_root_path,
            uv_sync_mode=UvSyncMode.UPGRADE,
        )
