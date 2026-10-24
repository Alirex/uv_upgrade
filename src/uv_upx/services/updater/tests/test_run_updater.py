from typing import TYPE_CHECKING

from typer.testing import CliRunner

from uv_upx.cli.main import app
from uv_upx.services.updater import UpdaterOptions, run_updater
from uv_upx.tests.fake_uv import FakeUv

if TYPE_CHECKING:
    import pathlib

    import pytest

PYPROJECT = """[project]
name = "demo"
version = "0.1.0"
dependencies = [
    # HTTP client
    "httpx>=0.24.0",
]
"""

LOCK_BEFORE = """version = 1

[[package]]
name = "httpx"
version = "0.24.0"
"""

LOCK_AFTER = LOCK_BEFORE.replace('"0.24.0"', '"0.28.1"')

UPGRADE = ["uv", "lock", "--upgrade"]
SYNC = ["uv", "sync", "--all-groups", "--all-extras", "--all-packages"]
SYNC_FROZEN = [*SYNC, "--frozen"]


def _project(root: pathlib.Path, lock: str = LOCK_BEFORE) -> tuple[pathlib.Path, pathlib.Path]:
    pyproject = root / "pyproject.toml"
    uv_lock = root / "uv.lock"
    _ = pyproject.write_text(PYPROJECT)
    _ = uv_lock.write_text(lock)
    return pyproject, uv_lock


def test_upgrade_writes_pyproject_and_syncs(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pyproject, uv_lock = _project(tmp_path)
    fake = FakeUv(lock_after_upgrade=LOCK_AFTER).install(monkeypatch)

    run_updater(project_root_path=tmp_path, options=UpdaterOptions())

    assert pyproject.read_text() == PYPROJECT.replace(">=0.24.0", ">=0.28.1")
    assert uv_lock.read_text() == LOCK_AFTER
    assert fake.commands == [UPGRADE, SYNC]


def test_no_sync_relocks_without_sync(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pyproject, _ = _project(tmp_path)
    fake = FakeUv(lock_after_upgrade=LOCK_AFTER).install(monkeypatch)

    run_updater(project_root_path=tmp_path, options=UpdaterOptions(no_sync=True))

    assert ">=0.28.1" in pyproject.read_text()
    assert fake.commands == [UPGRADE, ["uv", "lock"]]


def test_dry_run_restores_files(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pyproject, uv_lock = _project(tmp_path)
    fake = FakeUv(lock_after_upgrade=LOCK_AFTER).install(monkeypatch)

    run_updater(project_root_path=tmp_path, options=UpdaterOptions(dry_run=True))

    assert pyproject.read_text() == PYPROJECT
    assert uv_lock.read_text() == LOCK_BEFORE
    assert fake.commands == [UPGRADE, SYNC_FROZEN]


def test_nothing_to_upgrade_restores_lock(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    lock_up_to_date = LOCK_BEFORE + "\n# re-resolved\n"
    pyproject, uv_lock = _project(tmp_path)
    _ = FakeUv(lock_after_upgrade=lock_up_to_date).install(monkeypatch)

    run_updater(project_root_path=tmp_path, options=UpdaterOptions(no_sync=True))

    assert pyproject.read_text() == PYPROJECT
    assert uv_lock.read_text() == LOCK_BEFORE


def test_failed_sync_rolls_back(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pyproject, uv_lock = _project(tmp_path)
    fake = FakeUv(lock_after_upgrade=LOCK_AFTER, sync_fails=True).install(monkeypatch)

    run_updater(project_root_path=tmp_path, options=UpdaterOptions())

    assert pyproject.read_text() == PYPROJECT
    assert uv_lock.read_text() == LOCK_BEFORE
    assert fake.commands == [UPGRADE, SYNC, SYNC_FROZEN]


def test_failed_lock_rolls_back(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pyproject, uv_lock = _project(tmp_path)
    _ = FakeUv(lock_after_upgrade=LOCK_AFTER, lock_returncode=1, lock_stderr="error: No solution found\n").install(
        monkeypatch,
    )

    run_updater(project_root_path=tmp_path, options=UpdaterOptions(no_sync=True))

    assert pyproject.read_text() == PYPROJECT
    assert uv_lock.read_text() == LOCK_BEFORE


def test_cli_keep_unconstrained(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pyproject = tmp_path / "pyproject.toml"
    _ = pyproject.write_text(PYPROJECT.replace('"httpx>=0.24.0"', '"httpx"'))
    _ = (tmp_path / "uv.lock").write_text(LOCK_BEFORE)
    _ = FakeUv(lock_after_upgrade=LOCK_AFTER).install(monkeypatch)

    result = CliRunner().invoke(app, ["upgrade", "run", "--project", str(tmp_path), "--keep-unconstrained"])

    assert result.exit_code == 0, result.output
    assert pyproject.read_text() == PYPROJECT.replace('"httpx>=0.24.0"', '"httpx"')


def test_cli_dry_run(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pyproject, _ = _project(tmp_path)
    fake = FakeUv(lock_after_upgrade=LOCK_AFTER).install(monkeypatch)

    result = CliRunner().invoke(app, ["upgrade", "run", "--project", str(tmp_path), "--dry-run"])

    assert result.exit_code == 0, result.output
    assert pyproject.read_text() == PYPROJECT
    assert fake.commands == [UPGRADE, SYNC_FROZEN]
