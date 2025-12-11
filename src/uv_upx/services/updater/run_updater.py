import copy
import logging
from typing import TYPE_CHECKING

from uv_upx.services.dependencies_from_project import get_dependencies_from_project
from uv_upx.services.dependency_up.handle_groups import handle_py_projects
from uv_upx.services.get_all_pyprojects import get_all_pyprojects_by_project_root_path
from uv_upx.services.normalize_paths import get_and_check_path_to_uv_lock
from uv_upx.services.toml import toml_load
from uv_upx.services.updater.finalize_updating import finalize_updating
from uv_upx.services.updater.rollback_updater import rollback_updater
from uv_upx.services.updater.update_lock_file import update_lock_file

if TYPE_CHECKING:
    import pathlib


def run_updater(
    *,
    project_root_path: pathlib.Path,
    #
    dry_run: bool = False,
    verbose: bool = False,
    #
    preserve_original_package_names: bool = False,
    #
    no_sync: bool = False,
) -> None:
    logger = logging.getLogger(__name__)

    uv_lock_path = get_and_check_path_to_uv_lock(project_root_path)
    uv_lock_data = toml_load(uv_lock_path)
    uv_lock_data_copy = copy.deepcopy(uv_lock_data)

    py_projects = get_all_pyprojects_by_project_root_path(project_root_path)
    if verbose:
        logger.info(f"Found {len(py_projects.items)} pyproject.toml files in the workspace.")
        for py_project in py_projects.items:
            logger.info(f"  {py_project.path.as_uri()}")

    py_projects_copy = copy.deepcopy(py_projects)

    is_rollback_needed = dry_run
    rollback_message = "Rolling back to previous state because dry run is enabled."

    try:
        update_lock_file(
            project_root_path,
            no_sync=no_sync,
        )

        if handle_py_projects(
            py_projects=py_projects,
            dependencies_registry=get_dependencies_from_project(workdir=project_root_path),
            #
            dry_run=dry_run,
            verbose=verbose,
            #
            preserve_original_package_names=preserve_original_package_names,
        ):
            logger.info("Updated pyproject.toml files successfully.")

            finalize_updating(
                project_root_path,
                dry_run=dry_run,
                #
                no_sync=no_sync,
            )

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
                #
                no_sync=no_sync,
            )
            logger.info(rollback_message)
    except Exception as e:  # noqa: BLE001
        msg = f"Failed to rollback: '{e}'"
        logger.error(msg)  # noqa: TRY400
