import tomlkit
from tomlkit.items import Array

from uv_upx.services.toml import array_items, get_arrays_in_table, get_node, is_table, toml_dumps

PYPROJECT = """
[project]
name = "foo"
dependencies = [
    "httpx>=0.24.0",  # comment
    { include-group = "dev" },
]

[tool.ruff]
line-length = 120

[project.optional-dependencies]
cli = ["typer"]
not-an-array = "text"

[dependency-groups]
dev = ["pytest"]
"""


def test_get_node_returns_live_nodes() -> None:
    data = tomlkit.parse(PYPROJECT)

    node = get_node(data, "dependency-groups", "dev")

    assert isinstance(node, Array)
    node[0] = "pytest>=9"
    assert 'dev = ["pytest>=9"]' in toml_dumps(data)


def test_get_node_missing_path() -> None:
    data = tomlkit.parse(PYPROJECT)

    assert get_node(data, "missing") is None
    assert get_node(data, "project", "name", "deeper") is None
    assert get_node(data) is data


def test_get_node_through_out_of_order_table() -> None:
    # "[project]" is split in two places of the file by "[tool.ruff]".
    data = tomlkit.parse(PYPROJECT)

    node = get_node(data, "project", "optional-dependencies", "cli")

    assert isinstance(node, Array)
    assert array_items(node) == ["typer"]


def test_is_table() -> None:
    data = tomlkit.parse(PYPROJECT)

    assert is_table(data)
    assert is_table(get_node(data, "project"))
    assert not is_table(get_node(data, "project", "name"))
    assert not is_table(None)


def test_get_arrays_in_table_skips_not_arrays() -> None:
    data = tomlkit.parse(PYPROJECT)

    arrays = get_arrays_in_table(data, "project", "optional-dependencies")

    assert list(arrays) == ["cli"]
    assert get_arrays_in_table(data, "missing") == {}
    assert get_arrays_in_table(data, "project", "name") == {}


def test_array_items_keeps_order_and_non_strings() -> None:
    data = tomlkit.parse(PYPROJECT)
    dependencies = get_node(data, "project", "dependencies")
    assert isinstance(dependencies, Array)

    items = array_items(dependencies)

    assert items[0] == "httpx>=0.24.0"
    assert items[1] == {"include-group": "dev"}
