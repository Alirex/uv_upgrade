from typing import TYPE_CHECKING

import pytest
from safe_result import Err, Ok

from uv_upx.services.local_segments.constants import ERROR_TEXT_PART_I_NON_EMPTY_LOCAL_SEGMENT
from uv_upx.services.local_segments.exceptions import NonEmptyLocalSegmentsError
from uv_upx.services.run_uv_related import UnresolvedDependencyError, UvSyncMode, run_uv_lock, run_uv_sync
from uv_upx.tests.fake_uv import FakeUv

if TYPE_CHECKING:
    import pathlib


@pytest.mark.parametrize(
    ("upgrade", "expected"),
    [
        (False, ["uv", "lock"]),
        (True, ["uv", "lock", "--upgrade"]),
    ],
)
def test_run_uv_lock_ok(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    upgrade: bool,
    expected: list[str],
) -> None:
    fake = FakeUv(lock_after_upgrade="").install(monkeypatch)

    result = run_uv_lock(tmp_path, upgrade=upgrade)

    assert isinstance(result, Ok)
    assert fake.commands == [expected]


@pytest.mark.parametrize(
    ("stderr", "error_type"),
    [
        (f"error: {ERROR_TEXT_PART_I_NON_EMPTY_LOCAL_SEGMENT}\n", NonEmptyLocalSegmentsError),
        ("error: No solution found\n", UnresolvedDependencyError),
    ],
)
def test_run_uv_lock_error(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    stderr: str,
    error_type: type[Exception],
) -> None:
    _ = FakeUv(lock_after_upgrade="", lock_returncode=1, lock_stderr=stderr).install(monkeypatch)

    result = run_uv_lock(tmp_path)

    assert isinstance(result, Err)
    assert isinstance(result.error, error_type)
    # The output of uv is still shown to the user.
    assert capsys.readouterr().err == stderr


@pytest.mark.parametrize(
    ("mode", "include_all", "expected"),
    [
        (UvSyncMode.DEFAULT, True, ["uv", "sync", "--all-groups", "--all-extras", "--all-packages"]),
        (UvSyncMode.FROZEN, True, ["uv", "sync", "--all-groups", "--all-extras", "--all-packages", "--frozen"]),
        (UvSyncMode.UPGRADE, False, ["uv", "sync", "--upgrade"]),
    ],
)
def test_run_uv_sync_command(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: UvSyncMode,
    *,
    include_all: bool,
    expected: list[str],
) -> None:
    fake = FakeUv(lock_after_upgrade="").install(monkeypatch)

    run_uv_sync(tmp_path, mode, include_all=include_all)

    assert fake.commands == [expected]


def test_run_uv_sync_error(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ = FakeUv(lock_after_upgrade="", sync_fails=True).install(monkeypatch)

    with pytest.raises(UnresolvedDependencyError):
        run_uv_sync(tmp_path, UvSyncMode.DEFAULT)
