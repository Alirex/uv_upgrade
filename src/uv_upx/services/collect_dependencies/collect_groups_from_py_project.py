import itertools
import logging
from typing import TYPE_CHECKING

from tomlkit.items import Array

from uv_upx.services.collect_dependencies.models import DependencyGroup, DependencySection
from uv_upx.services.toml import get_arrays_in_table, get_node, is_table

if TYPE_CHECKING:
    from collections.abc import Iterable

    from tomlkit import TOMLDocument


# https://docs.astral.sh/uv/concepts/projects/dependencies/


def collect_i_main_dependency_group(
    data: TOMLDocument,
) -> Iterable[DependencyGroup]:
    """Check the main dependencies group."""
    logger = logging.getLogger(__name__)

    if "project" in data and not is_table(get_node(data, "project")):
        logger.warning("No [project] table found in pyproject.toml")
        return

    dependencies = get_node(data, "project", "dependencies")
    if not dependencies:
        return

    if not isinstance(dependencies, Array):
        logger.warning("No [project].dependencies found in pyproject.toml")
        return

    yield DependencyGroup(
        section=DependencySection.MAIN,
        dependencies=dependencies,
    )


def collect_i_dependency_groups(
    data: TOMLDocument,
) -> Iterable[DependencyGroup]:
    """Check the dependency-groups table.

    https://docs.astral.sh/uv/concepts/projects/dependencies/#development-dependencies
    """
    yield from collect_dependency_groups_i_many(
        groups=get_arrays_in_table(data, "dependency-groups"),
        section=DependencySection.DEPENDENCY_GROUPS,
    )


def collect_i_optional_dependencies(
    data: TOMLDocument,
) -> Iterable[DependencyGroup]:
    """Check the project.optional-dependencies table.

    https://docs.astral.sh/uv/concepts/projects/dependencies/#optional-dependencies
    """
    yield from collect_dependency_groups_i_many(
        groups=get_arrays_in_table(data, "project", "optional-dependencies"),
        section=DependencySection.OPTIONAL_DEPENDENCIES,
    )


def collect_dependency_groups_i_many(
    *,
    groups: dict[str, Array],
    #
    section: DependencySection,
) -> Iterable[DependencyGroup]:
    """Make dependency groups from the arrays of a table."""
    for group_name, dependencies in groups.items():
        yield DependencyGroup(
            section=section,
            group_name=group_name,
            dependencies=dependencies,
        )


def collect_from_py_project(
    data: TOMLDocument,
) -> Iterable[DependencyGroup]:
    yield from itertools.chain(
        collect_i_main_dependency_group(data=data),
        collect_i_dependency_groups(data=data),
        collect_i_optional_dependencies(data=data),
    )
