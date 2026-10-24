from typing import TYPE_CHECKING

from uv_upx.services.parse_v2.collect_dependencies import collect_top_level_dependencies

if TYPE_CHECKING:
    import pathlib


def test_workspace_members_are_skipped(tmp_path: pathlib.Path) -> None:
    _ = (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "root"
version = "0.1.0"
dependencies = [
    "Albert_Client",
    "context",
    "httpx>=0.24.0",
]

[tool.uv.sources]
albert-client = { workspace = true }
context = { workspace = true }

[tool.uv.workspace]
members = ["packages/*"]
""",
    )
    member_path = tmp_path / "packages" / "context"
    member_path.mkdir(parents=True)
    _ = (member_path / "pyproject.toml").write_text(
        """
[project]
name = "context"
version = "0.1.0"
dependencies = [
    "albert-client",
    "pydantic",
]
""",
    )

    collected = collect_top_level_dependencies(project_root_path=tmp_path)

    names = {
        py_project.path.parent.name: [
            str(dependency.parsed.package_name)
            for group in py_project.dependency_groups_parsed
            for dependency in group.parsed_dependencies
        ]
        for py_project in collected.parsed_pyprojects
    }
    assert names == {tmp_path.name: ["httpx"], "context": ["pydantic"]}
