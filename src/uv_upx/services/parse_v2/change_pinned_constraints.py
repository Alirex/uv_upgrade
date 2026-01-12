import copy
from typing import TYPE_CHECKING

from uv_upx.services.dependency_up.constants.operators import (
    VERSION_OPERATOR_I_EQUAL,
    VERSION_OPERATOR_I_GREATER_OR_EQUAL,
    VERSION_OPERATORS_I_PINNED_ALLOWED_TO_CHANGE,
    VERSION_OPERATORS_I_PUT_IF_DIFFERENT,
)
from uv_upx.services.local_segments.constants import LOCAL_SEGMENT_CHAR_INDICATOR
from uv_upx.services.toml import toml_save

if TYPE_CHECKING:
    from uv_upx.services.parse_v2.collect_dependencies import CollectedTopLevelDependencies


def change_pinned_constraints(
    collected_top_level_dependencies: CollectedTopLevelDependencies,
    #
    *,
    is_ignore_local_segments: bool = False,
) -> None:
    copied_dependencies = copy.deepcopy(collected_top_level_dependencies)

    for py_project in copied_dependencies.parsed_pyprojects:
        is_have_changes_for_file = False

        for group in py_project.dependency_groups_parsed:
            for dependency in group.parsed_dependencies:
                dependency_parsed = dependency.parsed

                is_have_changes_for_dependency = False
                for version_constraint in dependency_parsed.version_constraints:
                    if (
                        is_ignore_local_segments
                        and (version_constraint.operator in VERSION_OPERATORS_I_PUT_IF_DIFFERENT)
                        and (LOCAL_SEGMENT_CHAR_INDICATOR in version_constraint.version)
                    ):
                        version_constraint.operator = VERSION_OPERATOR_I_EQUAL
                        is_have_changes_for_dependency = True

                    elif version_constraint.operator in VERSION_OPERATORS_I_PINNED_ALLOWED_TO_CHANGE:
                        version_constraint.operator = VERSION_OPERATOR_I_GREATER_OR_EQUAL
                        is_have_changes_for_dependency = True

                if is_have_changes_for_dependency:
                    group.dependencies[dependency.index_in_group] = dependency_parsed.get_full_spec()
                    is_have_changes_for_file = True

        if is_have_changes_for_file:
            toml_save(py_project.path, py_project.data)
