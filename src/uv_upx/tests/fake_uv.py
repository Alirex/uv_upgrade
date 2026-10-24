"""A fake `uv` for tests: records the commands and plays `uv lock` and `uv sync` without the network."""

import dataclasses
import pathlib
import subprocess

import pytest

from uv_upx.services.normalize_paths import NAME_OF_UV_LOCK_FILE


@dataclasses.dataclass(kw_only=True)
class FakeUv:
    lock_after_upgrade: str
    """Written to `uv.lock` by `uv lock --upgrade`."""

    lock_returncode: int = 0
    lock_stderr: str = ""
    sync_fails: bool = False
    """`uv sync` fails, except the `--frozen` one of the rollback."""

    commands: list[list[str]] = dataclasses.field(default_factory=list[list[str]])

    def run(
        self,
        args: list[str],
        *,
        check: bool,
        cwd: pathlib.Path,
        **_options: object,
    ) -> subprocess.CompletedProcess[str]:
        self.commands.append(args)
        returncode = 0
        stderr = ""
        match args:
            case ["uv", "lock", *flags]:
                if "--upgrade" in flags:
                    _ = (cwd / NAME_OF_UV_LOCK_FILE).write_text(self.lock_after_upgrade)
                returncode = self.lock_returncode
                stderr = self.lock_stderr
            case ["uv", "sync", *flags] if self.sync_fails and "--frozen" not in flags:
                returncode = 1
            case _:
                pass

        completed = subprocess.CompletedProcess(args, returncode, stdout=None, stderr=stderr)
        if check:
            completed.check_returncode()
        return completed

    def install(self, monkeypatch: pytest.MonkeyPatch) -> FakeUv:
        monkeypatch.setattr(subprocess, "run", self.run)
        return self
