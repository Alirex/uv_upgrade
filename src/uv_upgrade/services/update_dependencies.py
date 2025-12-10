import logging
from typing import TYPE_CHECKING

from uv_upgrade.services.parse_dependency import parse_dependency

if TYPE_CHECKING:
    from uv_upgrade.services.get_deps_from_project import DependenciesRegistry

type IncludedDependencyGroup = dict[str, str]


def update_dependencies(  # noqa: C901, PLR0912
    *,
    deps_sequence_from_config: list[str] | list[str | IncludedDependencyGroup],
    dependencies_registry: DependenciesRegistry,
    verbose: bool = False,
) -> bool:
    """Update the list of dependencies.

    Update it in-place.
    Because we want to preserve the comments.

    Returns:
        True if there are changes, False otherwise.
    """
    logger = logging.getLogger(__name__)

    is_any_changed = False

    for _index, dep in enumerate(deps_sequence_from_config):
        if verbose:
            logger.info(f"Parsing dependency: {dep}")

        if not isinstance(dep, str):
            if verbose:
                # https://docs.astral.sh/uv/concepts/projects/dependencies/#nesting-groups
                logger.warning(f"Skipping non-string dependency: {dep}")
            continue

        parsed = parse_dependency(dep)

        if verbose:
            logger.info(f"Parsed dependency: {parsed}")

        try:
            version_new = dependencies_registry[parsed.dependency_name]
        except KeyError:
            continue

        if len(parsed.version_constraints) > 2:  # noqa: PLR2004
            msg = f"Multiple version constraints are not supported yet. Skip. Dependency: {dep}"
            if verbose:
                logger.warning(msg)

            continue

        if len(parsed.version_constraints) == 0:
            msg = f"No version constraints found. Skip. Dependency: {dep}"
            if verbose:
                logger.warning(msg)

            continue

        # Next work both for 1 and 2 version constraints

        version_constraint = parsed.version_constraints[0]
        if version_constraint.operator not in {">="}:
            msg = f"Operator {version_constraint.operator} is not supported yet. Skip. Dependency: {dep}"
            if verbose:
                logger.warning(msg)

            continue

        # Implement better version comparison logic here
        if version_new != version_constraint.version:
            version_constraint.version = version_new

            deps_sequence_from_config[_index] = parsed.get_full_spec()
            is_any_changed = True

    return is_any_changed
