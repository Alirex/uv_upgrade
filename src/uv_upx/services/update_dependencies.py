import copy
import logging
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel

from uv_upx.models.dependency_parsed import DependencyParsed
from uv_upx.services.parse_dependency import parse_dependency

if TYPE_CHECKING:
    from uv_upx.services.get_deps_from_project import DependenciesRegistry

type IncludedDependencyGroup = dict[str, str]


class ChangesItem(BaseModel):
    from_item: DependencyParsed
    to_item: DependencyParsed

    def __str__(self) -> str:
        return f"{self.from_item.get_full_spec()} -> {self.to_item.get_full_spec()}"


type ChangesList = list[ChangesItem]

VERSION_OPERATORS_I_PUT_IF_DIFFERENT: Final[set[str]] = {">="}

VERSION_OPERATORS_I_EXPLICIT_IGNORE: Final[set[str]] = {"=="}


def update_dependencies(  # noqa: C901, PLR0912
    *,
    deps_sequence_from_config: list[str] | list[str | IncludedDependencyGroup],
    dependencies_registry: DependenciesRegistry,
    verbose: bool = False,
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

        parsed = parse_dependency(dep)

        if verbose:
            logger.info(f"Parsed dependency: {parsed}")

        try:
            version_new = dependencies_registry[parsed.dependency_name]
        except KeyError as e:
            # Note: raise error, because it now we have all the dependencies in the registry.
            msg = f"Dependency not found in the registry: {parsed.dependency_name}"
            raise ValueError(msg) from e

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

        if is_has_changes:
            deps_sequence_from_config[_index] = parsed.get_full_spec()
            changes.append(ChangesItem(from_item=parsed_original, to_item=parsed))

    return changes
