import logging
from typing import TYPE_CHECKING

from uv_upx.services.run_uv_related import UvSyncMode, run_uv_lock, run_uv_sync

if TYPE_CHECKING:
    import pathlib


def check_updating_result(
    project_root_path: pathlib.Path,
    *,
    dry_run: bool = False,
    #
    no_sync: bool = False,
) -> None:
    logger = logging.getLogger(__name__)

    if dry_run:
        logger.info("Dry run. No changes were made.")

    elif no_sync:
        run_uv_lock(
            workdir=project_root_path,
        )
    else:
        # Because we want to re-check that all is ok.
        run_uv_sync(
            workdir=project_root_path,
            uv_sync_mode=UvSyncMode.FROZEN,
        )
        logger.info("Synced dependencies successfully.")
