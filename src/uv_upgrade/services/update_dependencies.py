import logging
from typing import TYPE_CHECKING

from uv_upgrade.services.parse_dependency import parse_dependency

if TYPE_CHECKING:
    from uv_upgrade.services.get_deps_by_venv import DependenciesRegistry


def update_dependencies(  # noqa: C901
    *,
    deps: list[str],
    new_deps: DependenciesRegistry,
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

    for _index, dep in enumerate(deps):
        if verbose:
            logger.info(f"Parsing dependency: {dep}")

        parsed = parse_dependency(dep)

        if verbose:
            logger.info(f"Parsed dependency: {parsed}")

        if len(parsed.version_constraints) > 1:
            msg = f"Multiple version constraints are not supported yet. Skip. Dependency: {dep}"
            if verbose:
                logger.warning(msg)

            continue

        if len(parsed.version_constraints) == 0:
            msg = f"No version constraints found. Skip. Dependency: {dep}"
            if verbose:
                logger.warning(msg)

            continue

        version_constraint = parsed.version_constraints[0]
        if version_constraint.operator not in {">="}:
            msg = f"Operator {version_constraint.operator} is not supported yet. Skip. Dependency: {dep}"
            if verbose:
                logger.warning(msg)

            continue

        version_new = new_deps.get(parsed.dependency_name)
        if version_new is None:
            continue

        # Implement better version comparison logic here
        if version_new != version_constraint.version:
            version_constraint.version = version_new

            deps[_index] = parsed.get_full_spec()
            is_any_changed = True

    return is_any_changed
