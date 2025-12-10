import copy
import logging
from typing import TYPE_CHECKING

from uv_upx.services.get_all_pyprojects import get_all_pyprojects
from uv_upx.services.get_deps_from_project import get_deps_from_project
from uv_upx.services.handle_groups import handle_py_projects
from uv_upx.services.normalize_and_check_path_to_pyproject import (
    get_and_check_path_to_uv_lock,
)
from uv_upx.services.rollback_updater import rollback_updater
from uv_upx.services.run_uv_lock import (
    run_uv_sync,
    run_uv_sync_upgrade,
)
from uv_upx.services.save_load_toml import load_toml

if TYPE_CHECKING:
    import pathlib


def run_updater(
    *,
    project_root_path: pathlib.Path,
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    logger = logging.getLogger(__name__)

    uv_lock_path = get_and_check_path_to_uv_lock(project_root_path)
    uv_lock_data = load_toml(uv_lock_path)
    uv_lock_data_copy = copy.deepcopy(uv_lock_data)

    py_projects = get_all_pyprojects(project_root_path)
    if verbose:
        logger.info(f"Found {len(py_projects.items)} pyproject.toml files in the workspace.")
        for py_project in py_projects.items:
            logger.info(f"  {py_project.path.as_uri()}")

    py_projects_copy = copy.deepcopy(py_projects)

    is_rollback_needed = dry_run
    rollback_message = "Rolling back to previous state because dry run is enabled."

    try:
        # Because we want to check build problems also.
        run_uv_sync_upgrade(workdir=project_root_path)

        dependencies_registry = get_deps_from_project(workdir=project_root_path)

        if handle_py_projects(
            py_projects=py_projects,
            dependencies_registry=dependencies_registry,
            #
            dry_run=dry_run,
            verbose=verbose,
        ):
            logger.info("Updated pyproject.toml files successfully.")

            if dry_run:
                logger.info("Dry run. No changes were made.")
            else:
                # run_uv_lock(workdir=project_root_path)
                # logger.info("Updated dependencies successfully.")

                # Because we want to re-check that all is ok.
                run_uv_sync(workdir=project_root_path)
                logger.info("Synced dependencies successfully.")

        else:
            msg = "No important changes detected. Rolling back to previous state."
            logger.info(msg)
            is_rollback_needed = True
            rollback_message = msg

    except Exception as e:  # noqa: BLE001
        msg = f"Failed to update dependencies: '{e}' Rolling back to previous state."
        logger.error(msg)  # noqa: TRY400
        is_rollback_needed = True
        rollback_message = msg

    try:
        if is_rollback_needed:
            rollback_updater(
                uv_lock_path=uv_lock_path,
                uv_lock_data=uv_lock_data_copy,
                #
                py_projects=py_projects_copy,
            )
            logger.info(rollback_message)
    except Exception as e:  # noqa: BLE001
        msg = f"Failed to rollback: '{e}'"
        logger.error(msg)  # noqa: TRY400
