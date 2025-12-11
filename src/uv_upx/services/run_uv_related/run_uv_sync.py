import enum
import subprocess
from typing import TYPE_CHECKING

from uv_upx.services.run_uv_related import UnresolvedDependencyError

if TYPE_CHECKING:
    import pathlib


class UvSyncMode(enum.Enum):
    UPGRADE = enum.auto()
    FROZEN = enum.auto()
    DEFAULT = enum.auto()


def run_uv_sync(
    workdir: pathlib.Path,
    uv_sync_mode: UvSyncMode,
    *,
    include_all: bool = True,
) -> None:
    # uv sync --all-groups --all-extras --all-packages --frozen
    command = ["uv", "sync"]
    if include_all:
        command.extend(["--all-groups", "--all-extras", "--all-packages"])

    match uv_sync_mode:
        case UvSyncMode.UPGRADE:
            command.append("--upgrade")
        case UvSyncMode.FROZEN:
            command.append("--frozen")
        case UvSyncMode.DEFAULT:
            pass

    try:
        subprocess.run(  # noqa: S603
            command,
            check=True,
            cwd=workdir,
        )
    except subprocess.CalledProcessError as e:
        msg = "Failed to sync dependencies with 'uv sync'. Please check your dependency specifications."
        raise UnresolvedDependencyError(
            msg,
        ) from e
