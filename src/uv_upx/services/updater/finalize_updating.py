import logging
from typing import TYPE_CHECKING

from safe_result import Err, Ok, safe_with

from uv_upx.services.local_segments.exceptions import NonEmptyLocalSegmentsError
from uv_upx.services.normalize_paths import get_and_check_path_to_uv_lock
from uv_upx.services.run_uv_related import UnresolvedDependencyError, UvSyncMode, run_uv_lock, run_uv_sync
from uv_upx.services.upgrade_profile import UpgradeProfile

if TYPE_CHECKING:
    import pathlib


# noinspection PyTypeChecker
@safe_with(UnresolvedDependencyError, NonEmptyLocalSegmentsError)
def finalize_updating(
    project_root_path: pathlib.Path,
    *,
    dry_run: bool = False,
    #
    no_sync: bool = False,
    #
    profile: UpgradeProfile = UpgradeProfile.DEFAULT,
    #
    interactive: bool = False,
) -> None:
    logger = logging.getLogger(__name__)

    if dry_run:
        logger.info("Dry run. No changes were made.")
        return

    if profile == UpgradeProfile.WITH_PINNED or interactive:
        uv_lock_path = get_and_check_path_to_uv_lock(project_root_path)
        uv_lock_path.unlink(missing_ok=True)

    if no_sync:
        match run_uv_lock(
            workdir=project_root_path,
        ):
            case Ok():
                pass
            case Err(e):
                raise e

        logger.info("Updated uv.lock successfully.")
    else:
        # Because we want to re-check that all is ok.
        run_uv_sync(
            workdir=project_root_path,
            uv_sync_mode=UvSyncMode.DEFAULT,
        )
        logger.info("Synced dependencies successfully with updating uv.lock.")
