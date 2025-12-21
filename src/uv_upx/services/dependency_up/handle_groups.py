import copy
import logging
from html import escape
from typing import TYPE_CHECKING

from prompt_toolkit import HTML, choice, print_formatted_text

from uv_upx.services.dependency_up.update_dependency import update_dependency_v2
from uv_upx.services.toml import toml_save
from uv_upx.services.upgrade_profile import UpgradeProfile

if TYPE_CHECKING:
    import pathlib

    from uv_upx.services.collect_dependencies.models import DependencyGroupParsed
    from uv_upx.services.dependencies_from_project import DependenciesRegistry
    from uv_upx.services.dependency_up import ChangesList
    from uv_upx.services.dependency_up.models.changes_list import ChangesItem
    from uv_upx.services.parse_v2.collect_dependencies import CollectedTopLevelDependencies, PyProjectWrapperExtra


def ask_interactive_confirmation(
    changes_item: ChangesItem,
    group: DependencyGroupParsed,
    path: pathlib.Path,
) -> bool:
    """Ask the user for confirmation in interactive mode."""
    print("=" * 40)
    print(f"In file: {path.as_uri()}")
    folder_name = path.parent.name
    print_formatted_text(HTML(f"Parent folder: <b>{folder_name}</b>"))

    group_title = str(group.section)
    if group.group_name:
        group_title += f"[{group.group_name}]"
    print_formatted_text(HTML(f"Group: <b>{group_title}</b>"))

    message = HTML(
        f"<ansiblue><b>{escape(changes_item.from_item.get_name_with_extras())}:</b></ansiblue> "
        f"<ansired>{escape(changes_item.from_item.get_partial_spec())}</ansired>"
        f" <ansiyellow>&#8594;</ansiyellow> "
        f"<ansigreen>{escape(changes_item.to_item.get_partial_spec())}</ansigreen>",
    )

    result = choice(
        message=message,
        options=[
            (True, "Accept"),
            (False, "Reject"),
        ],
        default=True,
        #
        enable_interrupt=True,
    )

    print("=" * 40)

    return result


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
        for dependency in group.parsed_dependencies:
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
                    # TODO: Rework this to avoid double update.
                    change_or_none = update_dependency_v2(
                        dependencies_registry=dependencies_registry,
                        parsed=dependency_parsed,
                        #
                        profile=profile,
                    )
                    if change_or_none is None:
                        msg = "Change should be applied, but it is not detected."
                        raise RuntimeError(msg)

                    changes.append(change_or_none)

                    group.dependencies[dependency.index_in_group] = dependency_parsed.get_full_spec()

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
        message = """You are running in interactive mode.
You will be prompted for each proposed change.

Note: These changes related to updating dependencies in pyproject.toml files.
It is implying how dependencies will be updated.
But, if you reject ">=X.Y.Z" change, it will not updated in pyproject.toml,
but it may still be updated in the lock file (e.g., uv.lock).
"""
        print(message)

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
