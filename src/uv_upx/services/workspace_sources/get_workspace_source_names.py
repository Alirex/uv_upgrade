from typing import TYPE_CHECKING

from uv_upx.services.package_name import PackageName
from uv_upx.services.uv_tool_config import read_uv_tool_config

if TYPE_CHECKING:
    from tomlkit import TOMLDocument


def get_workspace_source_names(data: TOMLDocument) -> set[PackageName]:
    """Names of packages that come from the uv workspace.

    They are listed in `[tool.uv.sources]` as `{ workspace = true }`.
    uv always resolves them to the local package, so a version constraint on them is meaningless.

    https://docs.astral.sh/uv/concepts/projects/dependencies/#workspace-member
    """
    sources = read_uv_tool_config(data).sources
    return {PackageName(name) for name, spec in sources.items() if spec is not None and spec.is_workspace}
