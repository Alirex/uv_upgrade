import logging
from typing import TYPE_CHECKING, Any

from uv_upgrade.services.save_load_toml import save_toml
from uv_upgrade.services.update_dependencies import IncludedDependencyGroup, update_dependencies

if TYPE_CHECKING:
    from tomlkit import TOMLDocument

    from uv_upgrade.services.get_all_pyprojects import PyProjectsRegistry, PyProjectWrapper
    from uv_upgrade.services.get_deps_from_project import DependenciesRegistry


# https://docs.astral.sh/uv/concepts/projects/dependencies/


def handle_main_dependency_group(
    *,
    data: TOMLDocument,
    dependencies_registry: DependenciesRegistry,
    verbose: bool = False,
) -> bool:
    """Check the main dependencies group.

    Return:
        True if there are changes, False otherwise.
    """
    logger = logging.getLogger(__name__)

    project: dict[Any, Any] = data.get("project", {})  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if not isinstance(project, dict):
        logger.warning("No [project] table found in pyproject.toml")
        return False

    dependencies: list[str] = project.get("dependencies", [])  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if not isinstance(dependencies, list):
        logger.warning("No [project].dependencies found in pyproject.toml")
        return False

    return update_dependencies(
        deps_sequence_from_config=dependencies,  # pyright: ignore[reportUnknownArgumentType]
        dependencies_registry=dependencies_registry,
        verbose=verbose,
    )


def handle_dependency_groups(
    *,
    data: TOMLDocument,
    dependencies_registry: DependenciesRegistry,
    verbose: bool = False,
) -> bool:
    """Check the dependency-groups table.

    https://docs.astral.sh/uv/concepts/projects/dependencies/#development-dependencies
    """
    return handle_dependency_groups_inner(
        groups=data.get("dependency-groups", {}),  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        dependencies_registry=dependencies_registry,
        verbose=verbose,
    )


def handle_optional_dependencies(
    *,
    data: TOMLDocument,
    dependencies_registry: DependenciesRegistry,
    verbose: bool = False,
) -> bool:
    """Check the project.optional-dependencies table.

    https://docs.astral.sh/uv/concepts/projects/dependencies/#optional-dependencies
    """
    return handle_dependency_groups_inner(
        groups=data.get("project", {}).get("optional-dependencies", {}),  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        dependencies_registry=dependencies_registry,
        verbose=verbose,
    )


def handle_dependency_groups_inner(
    *,
    groups: Any,  # noqa: ANN401
    dependencies_registry: DependenciesRegistry,
    verbose: bool = False,
) -> bool:
    """Check the dependency-groups table.

    https://docs.astral.sh/uv/concepts/projects/dependencies/#development-dependencies

    https://docs.astral.sh/uv/concepts/projects/dependencies/#optional-dependencies
    """
    logger = logging.getLogger(__name__)

    if not isinstance(groups, dict):
        return False

    dependency_groups: dict[str, Any] = groups  # pyright: ignore[reportUnknownVariableType]

    is_any_changed = False
    for _group_name, _group_val in dependency_groups.items():
        if verbose:
            logger.info(f"Checking group: {_group_name}")

        if not isinstance(_group_val, list):
            continue

        group_val: list[str | IncludedDependencyGroup] = _group_val  # pyright: ignore[reportUnknownVariableType]

        is_changed = update_dependencies(
            deps_sequence_from_config=group_val,
            dependencies_registry=dependencies_registry,
            verbose=verbose,
        )
        is_any_changed = is_any_changed or is_changed

    return is_any_changed


def handle_py_project(
    *,
    dependencies_registry: DependenciesRegistry,
    pyproject_wrapper: PyProjectWrapper,
    #
    dry_run: bool,
    verbose: bool,
) -> bool:
    """Handle a single pyproject.toml file.

    Return:
        True if there are changes, False otherwise.
    """
    logger = logging.getLogger(__name__)

    data = pyproject_wrapper.data

    is_changed_main = handle_main_dependency_group(
        data=data,
        dependencies_registry=dependencies_registry,
        verbose=verbose,
    )

    is_changed_groups = handle_dependency_groups(
        data=data,
        dependencies_registry=dependencies_registry,
        verbose=verbose,
    )

    is_changed_optional = handle_optional_dependencies(
        data=data,
        dependencies_registry=dependencies_registry,
        verbose=verbose,
    )

    is_changed_any = any([is_changed_main, is_changed_groups, is_changed_optional])

    if is_changed_any:
        if dry_run:
            logger.info(f"[Dry Run] Changes detected in {pyproject_wrapper.path.as_uri()}, but not saving.")
        else:
            save_toml(pyproject_wrapper.path, data)
            logger.info(f"Saved changes to {pyproject_wrapper.path.as_uri()}")

    return is_changed_any


def handle_py_projects(
    *,
    dependencies_registry: DependenciesRegistry,
    py_projects: PyProjectsRegistry,
    #
    dry_run: bool,
    verbose: bool,
) -> bool:
    """Handle multiple pyproject.toml files.

    Return:
        True if there are changes, False otherwise.
    """
    is_any_changed = False
    for py_project in py_projects.items:
        is_changed = handle_py_project(
            dependencies_registry=dependencies_registry,
            pyproject_wrapper=py_project,
            #
            dry_run=dry_run,
            verbose=verbose,
        )
        is_any_changed = is_any_changed or is_changed

    return is_any_changed
