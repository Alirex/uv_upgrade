import concurrent.futures
import logging
from typing import TYPE_CHECKING

from uv_upx.services.collect_dependencies.collect_groups_from_py_project import collect_from_py_project
from uv_upx.services.dependency_up import ChangesList, update_dependencies
from uv_upx.services.toml import toml_save

if TYPE_CHECKING:
    from uv_upx.services.dependencies_from_project import DependenciesRegistry
    from uv_upx.services.get_all_pyprojects import PyProjectsRegistry, PyProjectWrapper


def handle_py_project(
    *,
    dependencies_registry: DependenciesRegistry,
    pyproject_wrapper: PyProjectWrapper,
    #
    dry_run: bool,
    verbose: bool,
    #
    preserve_original_package_names: bool = False,
) -> ChangesList:
    """Handle a single pyproject.toml file."""
    logger = logging.getLogger(__name__)

    data = pyproject_wrapper.data

    changes: ChangesList = []

    for group in collect_from_py_project(data):
        changes_local = update_dependencies(
            deps_sequence_from_config=group.dependencies,
            dependencies_registry=dependencies_registry,
            #
            verbose=verbose,
            #
            preserve_original_package_names=preserve_original_package_names,
        )
        changes.extend(changes_local)

    if changes:
        if dry_run:
            logger.info(f"[Dry Run] Changes detected in {pyproject_wrapper.path.as_uri()}, but not saving.")
        else:
            toml_save(pyproject_wrapper.path, data)
            logger.info(f"Saved changes to {pyproject_wrapper.path.as_uri()}")

            for change in changes:
                logger.info(f"  {change}")

    return changes


def handle_py_projects(
    *,
    dependencies_registry: DependenciesRegistry,
    py_projects: PyProjectsRegistry,
    #
    dry_run: bool,
    verbose: bool,
    #
    preserve_original_package_names: bool = False,
) -> ChangesList:
    """Handle multiple pyproject.toml files."""
    changes: ChangesList = []

    # Note: don't really need threads here in this case.
    #   But this place can be one of the places to use parallelism.

    with concurrent.futures.ThreadPoolExecutor() as worker:
        tasks = [
            worker.submit(
                handle_py_project,
                dependencies_registry=dependencies_registry,
                pyproject_wrapper=py_project,
                #
                dry_run=dry_run,
                verbose=verbose,
                #
                preserve_original_package_names=preserve_original_package_names,
            )
            for py_project in py_projects.items
        ]
        for future in concurrent.futures.as_completed(tasks):
            changes_local = future.result()
            changes.extend(changes_local)

    return changes
