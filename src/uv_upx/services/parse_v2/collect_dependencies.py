import logging
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from uv_upx.services.collect_dependencies.collect_groups_from_py_project import collect_from_py_project
from uv_upx.services.collect_dependencies.models import (
    DependencyGroup,
    DependencyGroupParsed,
    DependencyItemParsed,
)
from uv_upx.services.dependency_up.parse_dependency import parse_dependency
from uv_upx.services.get_all_pyprojects import PyProjectWrapper, get_all_pyprojects_by_project_root_path
from uv_upx.services.toml import array_items
from uv_upx.services.workspace_sources import get_workspace_source_names

if TYPE_CHECKING:
    import pathlib

    from uv_upx.services.package_name import PackageName


class PyProjectWrapperExtra(PyProjectWrapper):
    dependency_groups_parsed: list[DependencyGroupParsed] = Field(
        default_factory=list,
    )


class CollectedTopLevelDependencies(BaseModel):
    parsed_pyprojects: list[PyProjectWrapperExtra]


def _parse_group_dependencies(
    group: DependencyGroup,
    *,
    workspace_source_names: set[PackageName],
    #
    preserve_original_package_names: bool,
    #
    verbose: bool,
) -> list[DependencyItemParsed]:
    """Parse the dependencies of one group. Skip nested groups and workspace members."""
    logger = logging.getLogger(__name__)

    parsed_dependencies: list[DependencyItemParsed] = []

    for index, dependency in enumerate(array_items(group.dependencies)):
        if not isinstance(dependency, str):
            if verbose:
                # https://docs.astral.sh/uv/concepts/projects/dependencies/#nesting-groups
                logger.warning("Skipping non-string dependency: %s", dependency)
            continue

        parsed = parse_dependency(
            dependency,
            preserve_original_package_names=preserve_original_package_names,
        )

        if parsed.package_name in workspace_source_names:
            if verbose:
                logger.info("Skipping workspace member: %s", dependency)
            continue

        parsed_dependencies.append(
            DependencyItemParsed(
                parsed=parsed,
                index_in_group=index,
            ),
        )

    return parsed_dependencies


def collect_top_level_dependencies(
    *,
    project_root_path: pathlib.Path,
    #
    preserve_original_package_names: bool = False,
    #
    verbose: bool = False,
) -> CollectedTopLevelDependencies:
    """Collect top-level dependencies from all pyproject.toml files in the project."""
    logger = logging.getLogger(__name__)

    if verbose:
        logger.info("Collect dependencies from project at: %s", project_root_path.as_uri())

    py_projects = get_all_pyprojects_by_project_root_path(project_root_path)

    # Note: The first item is the workspace root. Its sources apply to all members.
    root_workspace_source_names = get_workspace_source_names(py_projects.items[0].data)

    parsed_pyprojects: list[PyProjectWrapperExtra] = []
    for py_project in py_projects.items:
        workspace_source_names = root_workspace_source_names | get_workspace_source_names(py_project.data)

        dependency_groups_parsed: list[DependencyGroupParsed] = []

        for group in collect_from_py_project(py_project.data):
            parsed_dependencies = _parse_group_dependencies(
                group,
                workspace_source_names=workspace_source_names,
                preserve_original_package_names=preserve_original_package_names,
                verbose=verbose,
            )

            if not parsed_dependencies:
                continue

            dependency_group_parsed = DependencyGroupParsed(
                section=group.section,
                group_name=group.group_name,
                dependencies=group.dependencies,
                #
                parsed_dependencies=parsed_dependencies,
            )
            dependency_groups_parsed.append(dependency_group_parsed)

        if not dependency_groups_parsed:
            continue

        py_project_extra = PyProjectWrapperExtra(
            path=py_project.path,
            data=py_project.data,
            #
            dependency_groups_parsed=dependency_groups_parsed,
        )
        parsed_pyprojects.append(py_project_extra)

    return CollectedTopLevelDependencies(
        parsed_pyprojects=parsed_pyprojects,
    )
