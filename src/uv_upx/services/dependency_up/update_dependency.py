import copy
import logging
from typing import TYPE_CHECKING, Any

from uv_upx.services.dependency_up.constants.operators import (
    VERSION_OPERATOR_I_GREATER_OR_EQUAL,
    VERSION_OPERATORS_I_EXPLICIT_IGNORE,
    VERSION_OPERATORS_I_PINNED_ALLOWED_TO_CHANGE,
    VERSION_OPERATORS_I_PUT_IF_DIFFERENT,
)
from uv_upx.services.dependency_up.models.changes_list import ChangesItem
from uv_upx.services.dependency_up.models.dependency_parsed import DependencyParsed, VersionConstraint
from uv_upx.services.upgrade_profile import UpgradeProfile

if TYPE_CHECKING:
    from uv_upx.services.dependencies_from_project import DependenciesRegistry, Version


def update_dependency_v2(
    *,
    dependencies_registry: DependenciesRegistry,
    parsed: DependencyParsed,
    #
    profile: UpgradeProfile,
) -> ChangesItem | None:
    """Updates the dependency version based on registry lookup."""
    try:
        version_new = dependencies_registry[parsed.package_name]
    except KeyError:
        # Note: raise error, because it now we have all the dependencies in the registry.
        msg = f"Dependency not found in the registry: {parsed.package_name}"
        logger = logging.getLogger(__name__)
        logger.error(msg)  # noqa: TRY400
        return None

    parsed_original = copy.deepcopy(parsed)

    is_has_changes = False
    for version_constraint in parsed.version_constraints:
        is_has_changes_local = handle_version_constraint(
            version_constraint=version_constraint,
            version_new=version_new,
            #
            profile=profile,
        )
        if is_has_changes_local:
            is_has_changes = True

    if not parsed.version_constraints:
        parsed.version_constraints.append(
            VersionConstraint(operator=VERSION_OPERATOR_I_GREATER_OR_EQUAL, version=version_new),
        )
        is_has_changes = True

    if is_has_changes:
        return ChangesItem(
            from_item=parsed_original,
            to_item=parsed,
        )
    return None


type IsHasChanges = bool


def handle_version_constraint(
    *,
    version_constraint: VersionConstraint,
    version_new: Version,
    #
    profile: UpgradeProfile = UpgradeProfile.DEFAULT,
    #
    verbose: bool = False,
    dependency: Any | None = None,  # noqa: ANN401
) -> IsHasChanges:
    """Handle a single version constraint.

    Change it in-place. Because, for now, it is simpler than rebuilding the whole object.
    """
    logger = logging.getLogger(__name__)

    is_has_changes = False
    if version_constraint.operator in VERSION_OPERATORS_I_PUT_IF_DIFFERENT:
        # TODO: (?) Implement better version comparison logic here
        if version_constraint.version != version_new:
            version_constraint.version = version_new
            is_has_changes = True

    elif (profile is UpgradeProfile.WITH_PINNED) and (
        version_constraint.operator in VERSION_OPERATORS_I_PINNED_ALLOWED_TO_CHANGE
    ):
        # sourcery skip: hoist-similar-statement-from-if, hoist-statement-from-if
        if version_constraint.version != version_new:
            version_constraint.version = version_new
            is_has_changes = True
        # else:
        #     # Note: Workaround. Because we need to roll back the operator change.
        #     is_has_changes = True

    elif version_constraint.operator in VERSION_OPERATORS_I_EXPLICIT_IGNORE:
        if verbose and dependency:
            msg = f"Explicitly ignoring version constraint {version_constraint}. Dependency: {dependency}"
            logger.info(msg)
    elif verbose and dependency:
        msg = f"Operator {version_constraint.operator} is not supported yet. Skip. Dependency: {dependency}"
        logger.warning(msg)

    return is_has_changes
