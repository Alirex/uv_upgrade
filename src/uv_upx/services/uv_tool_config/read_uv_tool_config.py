from typing import TYPE_CHECKING

from uv_upx.services.uv_tool_config.models import PyProjectUvView, UvToolConfig

if TYPE_CHECKING:
    from tomlkit import TOMLDocument


def read_uv_tool_config(data: TOMLDocument) -> UvToolConfig:
    """Read `[tool.uv]` as validated typed data.

    It is a copy for reading. To change the file, use the original `TOMLDocument`: it keeps formatting and comments.
    """
    return PyProjectUvView.model_validate(data.unwrap()).tool.uv
