import logging
from typing import TYPE_CHECKING, Any

from uv_upx.services.toml import toml_save
from uv_upx.services.update_dependencies import ChangesList, IncludedDependencyGroup, update_dependencies

if TYPE_CHECKING:
    from tomlkit import TOMLDocument

    from uv_upx.services.dependencies_from_project import DependenciesRegistry
    from uv_upx.services.get_all_pyprojects import PyProjectsRegistry, PyProjectWrapper


# https://docs.astral.sh/uv/concepts/projects/dependencies/


def handle_main_dependency_group(
    *,
    data: TOMLDocument,
    dependencies_registry: DependenciesRegistry,
    verbose: bool = False,
) -> ChangesList:
    """Check the main dependencies group."""
    logger = logging.getLogger(__name__)

    project: dict[Any, Any] = data.get("project", {})  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if not isinstance(project, dict):
        logger.warning("No [project] table found in pyproject.toml")
        return []

    dependencies: list[str] = project.get("dependencies", [])  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if not isinstance(dependencies, list):
        logger.warning("No [project].dependencies found in pyproject.toml")
        return []

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
) -> ChangesList:
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
) -> ChangesList:
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
) -> ChangesList:
    """Check the dependency-groups table.

    https://docs.astral.sh/uv/concepts/projects/dependencies/#development-dependencies

    https://docs.astral.sh/uv/concepts/projects/dependencies/#optional-dependencies
    """
    logger = logging.getLogger(__name__)

    if not isinstance(groups, dict):
        return []

    dependency_groups: dict[str, Any] = groups  # pyright: ignore[reportUnknownVariableType]

    changes: ChangesList = []
    for _group_name, _group_val in dependency_groups.items():
        if verbose:
            logger.info(f"Checking group: {_group_name}")

        if not isinstance(_group_val, list):
            continue

        group_val: list[str | IncludedDependencyGroup] = _group_val  # pyright: ignore[reportUnknownVariableType]

        changes_local = update_dependencies(
            deps_sequence_from_config=group_val,
            dependencies_registry=dependencies_registry,
            verbose=verbose,
        )
        changes.extend(changes_local)

    return changes


def handle_py_project(
    *,
    dependencies_registry: DependenciesRegistry,
    pyproject_wrapper: PyProjectWrapper,
    #
    dry_run: bool,
    verbose: bool,
) -> ChangesList:
    """Handle a single pyproject.toml file."""
    logger = logging.getLogger(__name__)

    data = pyproject_wrapper.data

    changes: ChangesList = []

    changes.extend(
        handle_main_dependency_group(
            data=data,
            dependencies_registry=dependencies_registry,
            verbose=verbose,
        ),
    )

    changes.extend(
        handle_dependency_groups(
            data=data,
            dependencies_registry=dependencies_registry,
            verbose=verbose,
        ),
    )

    changes.extend(
        handle_optional_dependencies(
            data=data,
            dependencies_registry=dependencies_registry,
            verbose=verbose,
        ),
    )

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
) -> ChangesList:
    """Handle multiple pyproject.toml files."""
    changes: ChangesList = []
    for py_project in py_projects.items:
        changes_local = handle_py_project(
            dependencies_registry=dependencies_registry,
            pyproject_wrapper=py_project,
            #
            dry_run=dry_run,
            verbose=verbose,
        )

        changes.extend(changes_local)

    return changes
