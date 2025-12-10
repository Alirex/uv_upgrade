import pathlib
from typing import Any, cast

from pydantic import BaseModel, ConfigDict
from tomlkit import TOMLDocument

from uv_upx.services.get_pyproject_paths_by_globs import get_pyproject_paths_by_globs
from uv_upx.services.normalize_and_check_path_to_pyproject import get_and_check_path_to_pyproject
from uv_upx.services.save_load_toml import load_toml


class PyProjectWrapper(BaseModel):
    path: pathlib.Path
    data: TOMLDocument

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class PyProjectsRegistry(BaseModel):
    items: list[PyProjectWrapper]


def get_all_pyprojects(
    project_root_path: pathlib.Path,
) -> PyProjectsRegistry:
    """Find all pyproject.toml files in the project tree.

    Use `workspaces` from uv.
    """
    items: list[PyProjectWrapper] = []

    root_pyproject_path = get_and_check_path_to_pyproject(project_root_path)
    root_pyproject_data = load_toml(root_pyproject_path)
    items.append(PyProjectWrapper(path=root_pyproject_path, data=root_pyproject_data))

    # Get workspaces_config
    # https://docs.astral.sh/uv/concepts/projects/workspaces/

    # Example:
    # [tool.uv.workspace]
    # members = ["packages/*"]
    # exclude = ["packages/seeds"]

    # TODO: (?) Improve this place for efficiency

    workspaces_config: dict[str, Any] = root_pyproject_data.get("tool", {}).get("uv", {}).get("workspace", {})  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
    members_i_relative_glob_based: list[str] = cast("list[str]", workspaces_config.get("members", []))  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
    exclude_i_relative_glob_based: list[str] = cast("list[str]", workspaces_config.get("exclude", []))  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]

    # Use glob-based pattern matching to find all pyproject.toml files in the workspace
    members_paths_set = get_pyproject_paths_by_globs(project_root_path, members_i_relative_glob_based)
    exclude_paths_set = get_pyproject_paths_by_globs(project_root_path, exclude_i_relative_glob_based)

    result_paths_set = members_paths_set - exclude_paths_set

    for path in result_paths_set:
        data = load_toml(path)
        items.append(PyProjectWrapper(path=path, data=data))

    return PyProjectsRegistry(items=items)
