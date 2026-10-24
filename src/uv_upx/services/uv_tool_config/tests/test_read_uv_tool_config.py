import tomlkit

from uv_upx.services.uv_tool_config import read_uv_tool_config


def test_read_workspace() -> None:
    data = tomlkit.parse(
        """
[tool.uv.workspace]
members = ["packages/*"]
exclude = ["packages/seeds"]
""",
    )

    workspace = read_uv_tool_config(data).workspace

    assert workspace.members == ["packages/*"]
    assert workspace.exclude == ["packages/seeds"]


def test_read_defaults_without_uv_table() -> None:
    config = read_uv_tool_config(tomlkit.parse('[project]\nname = "foo"\n'))

    assert config.workspace.members == []
    assert config.workspace.exclude == []
    assert config.sources == {}


def test_read_sources_keeps_only_tables() -> None:
    data = tomlkit.parse(
        """
[tool.uv.sources]
a = { workspace = true }
b = { workspace = "yes" }
c = [{ index = "one", marker = "sys_platform == 'win32'" }, { index = "two" }]
d = { git = "https://example.com/d.git" }
""",
    )

    sources = read_uv_tool_config(data).sources

    assert {name: spec is not None and spec.is_workspace for name, spec in sources.items()} == {
        "a": True,
        "b": False,
        "c": False,
        "d": False,
    }
