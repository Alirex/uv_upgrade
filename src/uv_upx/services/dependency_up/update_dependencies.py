import copy
import logging
from typing import TYPE_CHECKING

from uv_upx.services.dependency_up.constants.operators import (
    VERSION_OPERATOR_I_GREATER_OR_EQUAL,
    VERSION_OPERATORS_I_EXPLICIT_IGNORE,
    VERSION_OPERATORS_I_PUT_IF_DIFFERENT,
)
from uv_upx.services.dependency_up.models.changes_list import ChangesItem, ChangesList
from uv_upx.services.dependency_up.models.dependency_parsed import VersionConstraint
from uv_upx.services.dependency_up.parse_dependency import parse_dependency

if TYPE_CHECKING:
    from uv_upx.services.dependencies_from_project import DependenciesRegistry
    from uv_upx.services.dependency_up import IncludedDependencyGroup


def update_dependencies(  # noqa: C901, PLR0912
    *,
    deps_sequence_from_config: list[str] | list[str | IncludedDependencyGroup],
    dependencies_registry: DependenciesRegistry,
    verbose: bool = False,
    #
    preserve_original_package_names: bool = False,
) -> ChangesList:
    """Update the list of dependencies.

    Update it in-place.
    Because we want to preserve the comments.
    """
    logger = logging.getLogger(__name__)

    changes: ChangesList = []
    for _index, dep in enumerate(deps_sequence_from_config):
        if verbose:
            logger.info(f"Parsing dependency: {dep}")

        if not isinstance(dep, str):
            if verbose:
                # https://docs.astral.sh/uv/concepts/projects/dependencies/#nesting-groups
                logger.warning(f"Skipping non-string dependency: {dep}")
            continue

        parsed = parse_dependency(
            dep,
            preserve_original_package_names=preserve_original_package_names,
        )

        if verbose:
            logger.info(f"Parsed dependency: {parsed}")

        try:
            version_new = dependencies_registry[parsed.package_name]
        except KeyError:
            # Note: raise error, because it now we have all the dependencies in the registry.
            msg = f"Dependency not found in the registry: {parsed.package_name}"
            logger.error(msg)  # noqa: TRY400
            continue

        parsed_original = copy.deepcopy(parsed)

        is_has_changes = False
        for version_constraint in parsed.version_constraints:
            if version_constraint.operator in VERSION_OPERATORS_I_PUT_IF_DIFFERENT:
                # TODO: (?) Implement better version comparison logic here
                if version_new != version_constraint.version:
                    version_constraint.version = version_new
                    is_has_changes = True

            elif version_constraint.operator in VERSION_OPERATORS_I_EXPLICIT_IGNORE:
                if verbose:
                    msg = f"Explicitly ignoring version constraint {version_constraint}. Dependency: {dep}"
                    logger.info(msg)
            else:
                if verbose:
                    msg = f"Operator {version_constraint.operator} is not supported yet. Skip. Dependency: {dep}"
                    logger.warning(msg)

                continue

        if not parsed.version_constraints:
            parsed.version_constraints.append(
                VersionConstraint(operator=VERSION_OPERATOR_I_GREATER_OR_EQUAL, version=version_new),
            )
            is_has_changes = True

        if is_has_changes:
            deps_sequence_from_config[_index] = parsed.get_full_spec()
            changes.append(ChangesItem(from_item=parsed_original, to_item=parsed))

    return changes
