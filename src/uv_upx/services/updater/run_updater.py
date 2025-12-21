import logging
from typing import TYPE_CHECKING

from uv_upx.services.dependencies_from_project import get_dependencies_from_project
from uv_upx.services.dependency_up.handle_groups import handle_py_projects_v2
from uv_upx.services.get_all_pyprojects import get_all_pyprojects_by_project_root_path
from uv_upx.services.normalize_paths import get_and_check_path_to_uv_lock
from uv_upx.services.parse_v2.change_pinned_constraints import change_pinned_constraints
from uv_upx.services.parse_v2.collect_dependencies import collect_top_level_dependencies
from uv_upx.services.toml import toml_load
from uv_upx.services.updater.finalize_updating import finalize_updating
from uv_upx.services.updater.rollback_updater import RollbackData, rollback_updater
from uv_upx.services.updater.update_lock_file import update_lock_file
from uv_upx.services.upgrade_profile import UpgradeProfile

if TYPE_CHECKING:
    import pathlib


def run_updater(  # noqa: PLR0913
    *,
    project_root_path: pathlib.Path,
    #
    dry_run: bool = False,
    verbose: bool = False,
    #
    preserve_original_package_names: bool = False,
    #
    no_sync: bool = False,
    #
    interactive: bool = False,
    #
    profile: UpgradeProfile = UpgradeProfile.DEFAULT,
) -> None:
    """Orchestrates dependency updates with rollback on failure."""
    logger = logging.getLogger(__name__)

    uv_lock_path = get_and_check_path_to_uv_lock(project_root_path)
    uv_lock_data = toml_load(uv_lock_path)

    py_projects = get_all_pyprojects_by_project_root_path(project_root_path)
    if verbose:
        logger.info(f"Found {len(py_projects.items)} pyproject.toml files in the workspace.")
        for py_project in py_projects.items:
            logger.info(f"  {py_project.path.as_uri()}")

    rollback_data = RollbackData.from_parts(
        uv_lock_path=uv_lock_path,
        uv_lock_data=uv_lock_data,
        #
        py_projects=py_projects,
    )

    is_rollback_needed = dry_run
    rollback_message = "Rolling back to previous state because dry run is enabled."

    collected_top_level_dependencies = collect_top_level_dependencies(
        project_root_path=project_root_path,
        #
        preserve_original_package_names=preserve_original_package_names,
    )

    if profile is UpgradeProfile.WITH_PINNED:
        change_pinned_constraints(
            collected_top_level_dependencies=collected_top_level_dependencies,
        )

    try:
        update_lock_file(
            project_root_path,
        )

        dependencies_registry = get_dependencies_from_project(workdir=project_root_path)

        if handle_py_projects_v2(
            collected_top_level_dependencies=collected_top_level_dependencies,
            dependencies_registry=dependencies_registry,
            #
            verbose=verbose,
            #
            profile=profile,
            #
            interactive=interactive,
        ):
            logger.info("Updated pyproject.toml files successfully.")

            finalize_updating(
                project_root_path,
                dry_run=dry_run,
                #
                no_sync=no_sync,
                #
                profile=profile,
                #
                interactive=interactive,
            )

        else:
            msg = "No important changes detected. Rolling back to previous state."
            logger.info(msg)
            is_rollback_needed = True
            rollback_message = msg

    except Exception as e:  # noqa: BLE001
        msg = f"Failed to update dependencies: '{type(e)}:{e}' Rolling back to previous state."
        logger.error(msg)  # noqa: TRY400
        is_rollback_needed = True
        rollback_message = msg

    if dry_run:
        rollback_message = "Dry run enabled, rolling back to previous state."
        is_rollback_needed = True

    try:
        if is_rollback_needed:
            rollback_updater(
                rollback_data=rollback_data,
                #
                no_sync=no_sync,
            )
            logger.info(rollback_message)
    except Exception as e:  # noqa: BLE001
        msg = f"Failed to rollback: '{e}'"
        logger.error(msg)  # noqa: TRY400
