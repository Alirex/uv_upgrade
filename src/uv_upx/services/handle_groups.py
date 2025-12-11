import enum
import itertools
import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from uv_upx.services.dependency_up import ChangesList, IncludedDependencyGroup, update_dependencies
from uv_upx.services.dependency_up.models.dependencies_list import TomlBasedDependenciesList
from uv_upx.services.toml import toml_save

if TYPE_CHECKING:
    from collections.abc import Iterable

    from tomlkit import TOMLDocument

    from uv_upx.services.dependencies_from_project import DependenciesRegistry
    from uv_upx.services.get_all_pyprojects import PyProjectsRegistry, PyProjectWrapper


# https://docs.astral.sh/uv/concepts/projects/dependencies/


class DependencySection(enum.StrEnum):
    MAIN = "project.dependencies"
    DEPENDENCY_GROUPS = "dependency-groups"
    OPTIONAL_DEPENDENCIES = "project.optional-dependencies"


class DependencyGroup(BaseModel):
    section: DependencySection
    group_name: str | None = None
    dependencies: TomlBasedDependenciesList


def handle_main_dependency_group(
    data: TOMLDocument,
) -> Iterable[DependencyGroup]:
    """Check the main dependencies group."""
    logger = logging.getLogger(__name__)

    project: dict[Any, Any] = data.get("project", {})  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if not isinstance(project, dict):
        logger.warning("No [project] table found in pyproject.toml")
        return

    dependencies: list[str] = project.get("dependencies", [])  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if not isinstance(dependencies, list):
        logger.warning("No [project].dependencies found in pyproject.toml")
        return

    yield DependencyGroup(
        section=DependencySection.MAIN,
        dependencies=dependencies,  # pyright: ignore[reportUnknownArgumentType]
    )


def handle_dependency_groups(
    data: TOMLDocument,
) -> Iterable[DependencyGroup]:
    """Check the dependency-groups table.

    https://docs.astral.sh/uv/concepts/projects/dependencies/#development-dependencies
    """
    yield from handle_dependency_groups_inner(
        groups=data.get("dependency-groups", {}),  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        section=DependencySection.DEPENDENCY_GROUPS,
    )


def handle_optional_dependencies(
    data: TOMLDocument,
) -> Iterable[DependencyGroup]:
    """Check the project.optional-dependencies table.

    https://docs.astral.sh/uv/concepts/projects/dependencies/#optional-dependencies
    """
    yield from handle_dependency_groups_inner(
        groups=data.get("project", {}).get("optional-dependencies", {}),  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        section=DependencySection.OPTIONAL_DEPENDENCIES,
    )


def handle_dependency_groups_inner(
    *,
    groups: Any,  # noqa: ANN401
    #
    section: DependencySection,
) -> Iterable[DependencyGroup]:
    """Check the dependency-groups table."""
    if not isinstance(groups, dict):
        return

    dependency_groups: dict[str, Any] = groups  # pyright: ignore[reportUnknownVariableType]

    for _group_name, _group_val in dependency_groups.items():
        if not isinstance(_group_val, list):
            continue

        group_val: list[str | IncludedDependencyGroup] = _group_val  # pyright: ignore[reportUnknownVariableType]

        yield DependencyGroup(section=section, group_name=_group_name, dependencies=group_val)


def collect_from_py_project(
    data: TOMLDocument,
) -> Iterable[DependencyGroup]:
    yield from itertools.chain(
        handle_main_dependency_group(data=data),
        handle_dependency_groups(data=data),
        handle_optional_dependencies(data=data),
    )


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
    for py_project in py_projects.items:
        changes_local = handle_py_project(
            dependencies_registry=dependencies_registry,
            pyproject_wrapper=py_project,
            #
            dry_run=dry_run,
            verbose=verbose,
            #
            preserve_original_package_names=preserve_original_package_names,
        )

        changes.extend(changes_local)

    return changes
