import logging
from typing import TYPE_CHECKING, Final

from uv_upx.services.collect_dependencies.collect_groups_from_py_project import collect_from_py_project
from uv_upx.services.dependency_up.constants.operators import VERSION_OPERATORS_I_PUT_IF_DIFFERENT
from uv_upx.services.dependency_up.parse_dependency import parse_dependency
from uv_upx.services.get_all_pyprojects import get_all_pyprojects_by_project_root_path

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Iterable

    from uv_upx.services.dependency_up.models.dependencies_list import TomlBasedDependenciesList
    from uv_upx.services.dependency_up.models.dependency_parsed import DependencyParsed

TAB_CHARS: Final[str] = "  "


def filter_dependencies(
    dependencies: TomlBasedDependenciesList,
    *,
    only_special_cases: bool = False,
    #
    preserve_original_package_names: bool = False,
) -> Iterable[DependencyParsed]:
    for dep in dependencies:  # pyright: ignore[reportUnknownVariableType]
        if not isinstance(dep, str):
            continue

        dependency_parsed = parse_dependency(
            dep,
            preserve_original_package_names=preserve_original_package_names,
        )
        if only_special_cases and (
            (dependency_parsed.marker is not None)  # Have marker. It is an unusual case.
            or (len(dependency_parsed.version_constraints) > 1)  # Have more than one version constraint. It's complex.
            or (len(dependency_parsed.version_constraints) == 0)  # No version constraints. It's strange.
            or (
                any(
                    vc.operator not in VERSION_OPERATORS_I_PUT_IF_DIFFERENT
                    for vc in dependency_parsed.version_constraints
                )
            )
        ):
            yield dependency_parsed

        continue


def collect_top_level_dependencies(
    *,
    project_root_path: pathlib.Path,
    only_special_cases: bool = False,
    preserve_original_package_names: bool = False,
) -> None:
    logger = logging.getLogger(__name__)

    logger.info("Collecting top level dependencies...")

    py_projects = get_all_pyprojects_by_project_root_path(project_root_path)

    for py_project in py_projects.items:
        is_py_project_info_shown = False

        # Iterates dependencies; prints project, group, and dependency info
        for group in collect_from_py_project(py_project.data):
            is_group_title_shown = False

            for dep in filter_dependencies(
                group.dependencies,
                only_special_cases=only_special_cases,
                preserve_original_package_names=preserve_original_package_names,
            ):
                if not is_py_project_info_shown:
                    print(py_project.path.as_uri())
                    is_py_project_info_shown = True

                if not is_group_title_shown:
                    group_title = str(group.section)
                    if group.group_name:
                        group_title += f"[{group.group_name}]"

                    print(f"{TAB_CHARS}{group_title}:")
                    is_group_title_shown = True

                print(f"{TAB_CHARS * 2}{dep.get_full_spec()}")

            if is_group_title_shown:
                print("-" * 10)

        if is_py_project_info_shown:
            print("=" * 20)

    logger.info("Done.")
