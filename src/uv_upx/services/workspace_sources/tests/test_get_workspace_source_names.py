import tomlkit

from uv_upx.services.package_name import PackageName
from uv_upx.services.workspace_sources import get_workspace_source_names


def test_get_workspace_source_names() -> None:
    data = tomlkit.parse(
        """
[tool.uv.sources]
Albert_Client = { workspace = true }
context = { workspace = true }
httpx = { git = "https://github.com/encode/httpx" }
local-lib = { path = "../local-lib" }
not-workspace = { workspace = false }
""",
    )
    assert get_workspace_source_names(data) == {PackageName("albert-client"), PackageName("context")}


def test_get_workspace_source_names_without_sources() -> None:
    data = tomlkit.parse(
        """
[project]
name = "foo"
""",
    )
    assert get_workspace_source_names(data) == set()
