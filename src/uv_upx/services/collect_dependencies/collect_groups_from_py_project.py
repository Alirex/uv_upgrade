import itertools
import logging
from typing import TYPE_CHECKING, Any

from tomlkit.items import Array, Table

from uv_upx.services.collect_dependencies.models import DependencyGroup, DependencySection

if TYPE_CHECKING:
    from collections.abc import Iterable

    from tomlkit import TOMLDocument


# https://docs.astral.sh/uv/concepts/projects/dependencies/


def collect_i_main_dependency_group(
    data: TOMLDocument,
) -> Iterable[DependencyGroup]:
    """Check the main dependencies group."""
    logger = logging.getLogger(__name__)

    project: dict[Any, Any] = data.get("project", {})  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

    if not isinstance(project, dict):
        logger.warning("No [project] table found in pyproject.toml")
        return

    dependencies = project.get("dependencies", [])  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if not dependencies:
        return

    if not isinstance(dependencies, Array):
        logger.warning("No [project].dependencies found in pyproject.toml")
        return

    yield DependencyGroup(
        section=DependencySection.MAIN,
        dependencies=dependencies,  # pyright: ignore[reportUnknownArgumentType]
    )


def collect_i_dependency_groups(
    data: TOMLDocument,
) -> Iterable[DependencyGroup]:
    """Check the dependency-groups table.

    https://docs.astral.sh/uv/concepts/projects/dependencies/#development-dependencies
    """
    if groups := data.get("dependency-groups", {}):  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        yield from collect_dependency_groups_i_many(
            groups=groups,  # pyright: ignore[reportUnknownArgumentType]
            section=DependencySection.DEPENDENCY_GROUPS,
        )
    else:
        return


def collect_i_optional_dependencies(
    data: TOMLDocument,
) -> Iterable[DependencyGroup]:
    """Check the project.optional-dependencies table.

    https://docs.astral.sh/uv/concepts/projects/dependencies/#optional-dependencies
    """
    if groups := data.get("project", {}).get("optional-dependencies", {}):  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        yield from collect_dependency_groups_i_many(
            groups=groups,  # pyright: ignore[reportUnknownArgumentType]
            section=DependencySection.OPTIONAL_DEPENDENCIES,
        )
    else:
        return


def collect_dependency_groups_i_many(
    *,
    groups: Table,
    #
    section: DependencySection,
) -> Iterable[DependencyGroup]:
    """Check the dependency-groups table."""
    for group_name, _group_val in groups.items():  # pyright: ignore[reportUnknownVariableType]
        if not isinstance(_group_val, Array):
            continue

        group_val = _group_val  # pyright: ignore[reportUnknownVariableType]

        yield DependencyGroup(
            section=section,
            group_name=group_name,  # pyright: ignore[reportUnknownArgumentType]
            dependencies=group_val,
        )


def collect_from_py_project(
    data: TOMLDocument,
) -> Iterable[DependencyGroup]:
    yield from itertools.chain(
        collect_i_main_dependency_group(data=data),
        collect_i_dependency_groups(data=data),
        collect_i_optional_dependencies(data=data),
    )
