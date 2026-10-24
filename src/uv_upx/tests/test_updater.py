import pathlib  # noqa: TC003

from uv_upx.services.dependencies_from_project.parse_from_uv_lock_file import parse_from_uv_lock_file
from uv_upx.services.dependency_up.handle_groups import handle_py_projects_v2
from uv_upx.services.parse_v2.collect_dependencies import collect_top_level_dependencies
from uv_upx.services.upgrade_profile import UpgradeProfile

LOCK_FILE_CONTENTS = """
[[package]]
name = "httpx"
version = "0.28.1"

[[package]]
name = "pydantic"
version = "2.12.5"

[[package]]
name = "pytest"
version = "9.0.1"

[[package]]
name = "rich"
version = "14.2.0"
"""

ROOT_PYPROJECT = """[project]
name = "root"
version = "0.1.0"
dependencies = [
    # HTTP client
    "httpx>=0.24.0",
    "context",
]

[project.optional-dependencies]
cli = ["rich"]

[dependency-groups]
dev = [
    "pytest>=8.0",
    { include-group = "lint" },
]
lint = []

[tool.uv.sources]
context = { workspace = true }

[tool.uv.workspace]
members = ["packages/*"]
"""

MEMBER_PYPROJECT = """[project]
name = "context"
version = "0.1.0"
dependencies = [
    "pydantic==2.0.0",
    "httpx",
]
"""


def _write_workspace(root: pathlib.Path) -> pathlib.Path:
    (root / "pyproject.toml").write_text(ROOT_PYPROJECT)
    member = root / "packages" / "context"
    member.mkdir(parents=True)
    (member / "pyproject.toml").write_text(MEMBER_PYPROJECT)
    return member


def _upgrade(root: pathlib.Path, profile: UpgradeProfile) -> list[str]:
    changes = handle_py_projects_v2(
        dependencies_registry=parse_from_uv_lock_file(LOCK_FILE_CONTENTS),
        collected_top_level_dependencies=collect_top_level_dependencies(project_root_path=root),
        verbose=False,
        profile=profile,
    )
    return sorted(str(change) for change in changes)


def test_upgrade_workspace(tmp_path: pathlib.Path) -> None:
    member = _write_workspace(tmp_path)

    changes = _upgrade(tmp_path, UpgradeProfile.DEFAULT)

    assert changes == [
        "httpx:  -> >=0.28.1",
        "httpx: >=0.24.0 -> >=0.28.1",
        "pytest: >=8.0 -> >=9.0.1",
        "rich:  -> >=14.2.0",
    ]
    # Workspace member "context" is untouched, comments and nested groups are kept.
    assert (tmp_path / "pyproject.toml").read_text() == (
        ROOT_PYPROJECT.replace('"httpx>=0.24.0"', '"httpx>=0.28.1"')
        .replace('["rich"]', '["rich>=14.2.0"]')
        .replace('"pytest>=8.0"', '"pytest>=9.0.1"')
    )
    # Pinned versions are kept with the default profile.
    assert (member / "pyproject.toml").read_text() == MEMBER_PYPROJECT.replace('"httpx"', '"httpx>=0.28.1"')


def test_upgrade_workspace_with_pinned(tmp_path: pathlib.Path) -> None:
    member = _write_workspace(tmp_path)

    _upgrade(tmp_path, UpgradeProfile.WITH_PINNED)

    assert '"pydantic==2.12.5"' in (member / "pyproject.toml").read_text()
