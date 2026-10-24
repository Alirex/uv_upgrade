from typing import TYPE_CHECKING

from uv_upx.services.get_all_pyprojects.get_pyproject_paths_by_globs import get_pyproject_paths_by_globs
from uv_upx.services.get_all_pyprojects.models import PyProjectsRegistry, PyProjectWrapper
from uv_upx.services.normalize_paths import get_and_check_path_to_pyproject
from uv_upx.services.toml import toml_load
from uv_upx.services.uv_tool_config import read_uv_tool_config

if TYPE_CHECKING:
    import pathlib


def get_all_pyprojects_by_project_root_path(
    project_root_path: pathlib.Path,
) -> PyProjectsRegistry:
    """Find all pyproject.toml files in the project tree.

    Use `workspaces` from uv.

    Respect `exclude` patterns.
    """
    items: list[PyProjectWrapper] = []

    root_pyproject_path = get_and_check_path_to_pyproject(project_root_path)
    root_pyproject_data = toml_load(root_pyproject_path)
    items.append(PyProjectWrapper(path=root_pyproject_path, data=root_pyproject_data))

    # Get workspaces_config: `members` and `exclude` of `[tool.uv.workspace]`, for example
    # members = ["packages/*"] and exclude = ["packages/seeds"].
    # https://docs.astral.sh/uv/concepts/projects/workspaces/

    # TODO: (?) Improve this place for efficiency

    workspace_config = read_uv_tool_config(root_pyproject_data).workspace

    # Use glob-based pattern matching to find all pyproject.toml files in the workspace
    members_paths_set = get_pyproject_paths_by_globs(project_root_path, workspace_config.members)
    exclude_paths_set = get_pyproject_paths_by_globs(project_root_path, workspace_config.exclude)

    result_paths_set = members_paths_set - exclude_paths_set

    for path in result_paths_set:
        data = toml_load(path)
        items.append(PyProjectWrapper(path=path, data=data))

    return PyProjectsRegistry(items=items)
