import copy
import logging
from typing import TYPE_CHECKING

from uv_upx.services.collect_dependencies.models import DependencyItemParsed
from uv_upx.services.dependency_up.ask_interactive_confirmation import (
    ask_interactive_confirmation,
    show_interactive_information,
)
from uv_upx.services.dependency_up.update_dependency import update_dependency_v2
from uv_upx.services.toml import toml_save
from uv_upx.services.upgrade_profile import UpgradeProfile

if TYPE_CHECKING:
    from uv_upx.services.dependencies_from_project import DependenciesRegistry
    from uv_upx.services.dependency_up import ChangesList
    from uv_upx.services.parse_v2.collect_dependencies import CollectedTopLevelDependencies, PyProjectWrapperExtra


def handle_py_project_v2(
    *,
    dependencies_registry: DependenciesRegistry,
    py_project: PyProjectWrapperExtra,
    #
    verbose: bool,
    #
    profile: UpgradeProfile,
    #
    interactive: bool = False,
) -> ChangesList:
    """Handle a single pyproject.toml file."""
    logger = logging.getLogger(__name__)

    data = py_project.data

    changes: ChangesList = []

    # TODO: Optimize.

    for group in py_project.dependency_groups_parsed:
        for index, dependency in enumerate(group.parsed_dependencies):
            dependency_parsed = dependency.parsed

            dependency_candidate = copy.deepcopy(dependency_parsed)

            change_or_none = update_dependency_v2(
                dependencies_registry=dependencies_registry,
                parsed=dependency_candidate,
                #
                profile=profile,
            )
            if change_or_none is not None:
                apply_change = True
                if interactive:
                    apply_change = ask_interactive_confirmation(
                        changes_item=change_or_none,
                        group=group,
                        path=py_project.path,
                    )

                if apply_change:
                    changes.append(change_or_none)
                    group.parsed_dependencies[index] = DependencyItemParsed(
                        index_in_group=dependency.index_in_group,
                        parsed=dependency_candidate,
                    )

                    group.dependencies[dependency.index_in_group] = dependency_candidate.get_full_spec()

                elif verbose:
                    logger.info(
                        f"Skipped change for {dependency_parsed.package_name} in {py_project.path.as_uri()}",
                    )

    if changes or (profile is UpgradeProfile.WITH_PINNED):
        # Note: "(profile is UpgradeProfile.WITH_PINNED)" require some way to write back changes.
        toml_save(py_project.path, data)
        logger.info(f"Saved changes to {py_project.path.as_uri()}")

        for change in changes:
            logger.info(f"  {change}")

    return changes


def handle_py_projects_v2(
    *,
    dependencies_registry: DependenciesRegistry,
    collected_top_level_dependencies: CollectedTopLevelDependencies,
    #
    verbose: bool,
    #
    profile: UpgradeProfile,
    #
    interactive: bool = False,
) -> ChangesList:
    """Handle multiple pyproject.toml files."""
    changes: ChangesList = []

    if interactive:
        show_interactive_information()

    for py_project in collected_top_level_dependencies.parsed_pyprojects:
        changes_local = handle_py_project_v2(
            dependencies_registry=dependencies_registry,
            py_project=py_project,
            #
            verbose=verbose,
            #
            profile=profile,
            #
            interactive=interactive,
        )
        changes.extend(changes_local)

    return changes
