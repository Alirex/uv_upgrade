import logging
from typing import TYPE_CHECKING, Any

from uv_upgrade.services.update_dependencies import update_dependencies

if TYPE_CHECKING:
    from tomlkit import TOMLDocument

    from uv_upgrade.services.get_deps_by_venv import DependenciesRegistry


def handle_main_dependency_group(
    *,
    data: TOMLDocument,
    new_deps: DependenciesRegistry,
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
        deps=dependencies,  # pyright: ignore[reportUnknownArgumentType]
        new_deps=new_deps,
        verbose=verbose,
    )


def handle_dependency_groups(
    *,
    data: TOMLDocument,
    new_deps: DependenciesRegistry,
    verbose: bool = False,
) -> bool:
    """Check the dependency-groups table."""
    logger = logging.getLogger(__name__)

    _dependency_groups = data.get("dependency-groups", {})  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]

    if not isinstance(_dependency_groups, dict):
        return False

    dependency_groups: dict[str, Any] = _dependency_groups  # pyright: ignore[reportUnknownVariableType]

    is_any_changed = False
    for _group_name, _group_val in dependency_groups.items():
        if verbose:
            logger.info(f"Checking group: {_group_name}")

        if not isinstance(_group_val, list):
            continue

        group_val: list[str] = _group_val  # pyright: ignore[reportUnknownVariableType]

        is_changed = update_dependencies(deps=group_val, new_deps=new_deps, verbose=verbose)
        is_any_changed = is_any_changed or is_changed

    return is_any_changed
