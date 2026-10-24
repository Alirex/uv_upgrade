import logging
from typing import TYPE_CHECKING

from safe_result import Err, Ok

from uv_upx.services.dependencies_from_project import get_dependencies_from_project
from uv_upx.services.dependency_up.handle_groups import handle_py_projects_v2
from uv_upx.services.dependency_up.models.update_options import DependencyUpdateOptions
from uv_upx.services.get_all_pyprojects import get_all_pyprojects_by_project_root_path
from uv_upx.services.local_segments.exceptions import NonEmptyLocalSegmentsError
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

    from uv_upx.services.parse_v2.collect_dependencies import CollectedTopLevelDependencies
    from uv_upx.services.updater.options import UpdaterOptions

LOCAL_SEGMENTS_MESSAGE = " ".join(
    (
        "Cannot proceed with pinned profile because there are local segments present.",
        "We rollback and try again with pinning constraints with local segments.",
    ),
)


def _update_lock_file_with_fallback(
    *,
    project_root_path: pathlib.Path,
    collected_top_level_dependencies: CollectedTopLevelDependencies,
    rollback_data: RollbackData,
    options: UpdaterOptions,
) -> None:
    """Update `uv.lock`. Raise on failure."""
    logger = logging.getLogger(__name__)

    match update_lock_file(
        project_root_path,
    ):
        case Ok():
            pass
        case Err(NonEmptyLocalSegmentsError()):
            # Note: Workaround for dependencies with local segments.
            logger.error(LOCAL_SEGMENTS_MESSAGE)

            rollback_updater(
                rollback_data=rollback_data,
                #
                no_sync=options.no_sync,
            )

            change_pinned_constraints(
                collected_top_level_dependencies=collected_top_level_dependencies,
                is_ignore_local_segments=True,
            )

            update_lock_file(
                project_root_path,
            ).unwrap()

        case Err(e):
            raise e


def _apply_updates(
    *,
    project_root_path: pathlib.Path,
    collected_top_level_dependencies: CollectedTopLevelDependencies,
    rollback_data: RollbackData,
    options: UpdaterOptions,
) -> bool:
    """Update the lock file and the pyproject.toml files. Raise on failure.

    Return `False`, if there are no important changes.
    """
    logger = logging.getLogger(__name__)

    _update_lock_file_with_fallback(
        project_root_path=project_root_path,
        collected_top_level_dependencies=collected_top_level_dependencies,
        rollback_data=rollback_data,
        options=options,
    )

    dependencies_registry = get_dependencies_from_project(workdir=project_root_path)

    if not handle_py_projects_v2(
        collected_top_level_dependencies=collected_top_level_dependencies,
        dependencies_registry=dependencies_registry,
        #
        verbose=options.verbose,
        #
        interactive=options.interactive,
        #
        update_options=DependencyUpdateOptions(
            profile=options.profile,
            keep_unconstrained=options.keep_unconstrained,
        ),
    ):
        return False

    logger.info("Updated pyproject.toml files successfully.")

    finalize_updating(
        project_root_path,
        dry_run=options.dry_run,
        #
        no_sync=options.no_sync,
        #
        profile=options.profile,
        #
        interactive=options.interactive,
    ).unwrap()

    return True


def run_updater(
    *,
    project_root_path: pathlib.Path,
    #
    options: UpdaterOptions,
) -> None:
    """Orchestrates dependency updates with rollback on failure."""
    logger = logging.getLogger(__name__)

    uv_lock_path = get_and_check_path_to_uv_lock(project_root_path)
    uv_lock_data = toml_load(uv_lock_path)

    py_projects = get_all_pyprojects_by_project_root_path(project_root_path)
    if options.verbose:
        logger.info("Found %d pyproject.toml files in the workspace.", len(py_projects.items))
        for py_project in py_projects.items:
            logger.info("  %s", py_project.path.as_uri())

    rollback_data = RollbackData.from_parts(
        uv_lock_path=uv_lock_path,
        uv_lock_data=uv_lock_data,
        #
        py_projects=py_projects,
    )

    is_rollback_needed = options.dry_run
    rollback_message = "Rolling back to previous state because dry run is enabled."

    collected_top_level_dependencies = collect_top_level_dependencies(
        project_root_path=project_root_path,
        #
        preserve_original_package_names=options.preserve_original_package_names,
    )

    if options.profile is UpgradeProfile.WITH_PINNED:
        change_pinned_constraints(
            collected_top_level_dependencies=collected_top_level_dependencies,
        )

    try:
        is_updated = _apply_updates(
            project_root_path=project_root_path,
            collected_top_level_dependencies=collected_top_level_dependencies,
            rollback_data=rollback_data,
            options=options,
        )
    # Any failure must lead to the rollback, so all exceptions are caught (and logged with the traceback).
    except Exception as e:
        msg = f"Failed to update dependencies: '{type(e)}:{e}' Rolling back to previous state."
        logger.exception(msg)
        is_rollback_needed = True
        rollback_message = msg
    else:
        if not is_updated:
            msg = "No important changes detected. Rolling back to previous state."
            logger.info(msg)
            is_rollback_needed = True
            rollback_message = msg

    if options.dry_run:
        rollback_message = "Dry run enabled, rolling back to previous state."
        is_rollback_needed = True

    try:
        if is_rollback_needed:
            rollback_updater(
                rollback_data=rollback_data,
                #
                no_sync=options.no_sync,
            )
            logger.info(rollback_message)
    except Exception as e:
        msg = f"Failed to rollback: '{e}'"
        logger.exception(msg)
