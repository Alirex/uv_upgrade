from typing import TYPE_CHECKING

from uv_upx.services.dependency_up.update_dependency import update_dependency

if TYPE_CHECKING:
    from uv_upx.services.dependencies_from_project import DependenciesRegistry
    from uv_upx.services.dependency_up.models.changes_list import ChangesList
    from uv_upx.services.dependency_up.models.dependencies_list import TomlBasedDependenciesList


def update_dependencies(
    *,
    deps_sequence_from_config: TomlBasedDependenciesList,
    dependencies_registry: DependenciesRegistry,
    #
    verbose: bool = False,
    #
    preserve_original_package_names: bool = False,
) -> ChangesList:
    """Update the list of dependencies.

    Update it in-place.
    Because we want to preserve the comments.
    """
    changes: ChangesList = []
    for index, dependency in enumerate(deps_sequence_from_config):
        changes_or_none = update_dependency(
            dependencies_registry=dependencies_registry,
            dependency=dependency,
            #
            verbose=verbose,
            #
            preserve_original_package_names=preserve_original_package_names,
        )

        if changes_or_none is not None:
            deps_sequence_from_config[index] = changes_or_none.to_item.get_full_spec()
            changes.append(changes_or_none)

    return changes
