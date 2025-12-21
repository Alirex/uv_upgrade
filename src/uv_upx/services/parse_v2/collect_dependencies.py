import logging
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from uv_upx.services.collect_dependencies.collect_groups_from_py_project import collect_from_py_project
from uv_upx.services.collect_dependencies.models import (
    DependencyGroupParsed,
    DependencyItemParsed,
)
from uv_upx.services.dependency_up.parse_dependency import parse_dependency
from uv_upx.services.get_all_pyprojects import PyProjectWrapper, get_all_pyprojects_by_project_root_path

if TYPE_CHECKING:
    import pathlib


class PyProjectWrapperExtra(PyProjectWrapper):
    dependency_groups_parsed: list[DependencyGroupParsed] = Field(
        default_factory=list,
    )


class CollectedTopLevelDependencies(BaseModel):
    parsed_pyprojects: list[PyProjectWrapperExtra]


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
        logger.info(f"Collect dependencies from project at: {project_root_path.as_uri()}")

    py_projects = get_all_pyprojects_by_project_root_path(project_root_path)

    parsed_pyprojects: list[PyProjectWrapperExtra] = []
    for py_project in py_projects.items:
        dependency_groups_parsed: list[DependencyGroupParsed] = []

        for group in collect_from_py_project(py_project.data):
            # Note: With this we can show the string representation of dependencies. With comments.
            # print(group.dependencies.as_string())

            parsed_dependencies: list[DependencyItemParsed] = []

            for index, dependency in enumerate(group.dependencies):
                if not isinstance(dependency, str):
                    if verbose:
                        # https://docs.astral.sh/uv/concepts/projects/dependencies/#nesting-groups
                        logger.warning(f"Skipping non-string dependency: {dependency}")
                    continue

                parsed = parse_dependency(
                    dependency,
                    preserve_original_package_names=preserve_original_package_names,
                )

                parsed_dependencies.append(
                    DependencyItemParsed(
                        parsed=parsed,
                        index_in_group=index,
                    ),
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


# for index, _dependency in enumerate(deps_sequence_from_config):
#     if changes_or_none is not None:
#         deps_sequence_from_config[index] = changes_or_none.to_item.get_full_spec()
