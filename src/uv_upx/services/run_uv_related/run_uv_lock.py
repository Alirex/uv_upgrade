import subprocess
import sys
from typing import TYPE_CHECKING

from safe_result import safe_with

from uv_upx.services.local_segments.constants import ERROR_TEXT_PART_I_NON_EMPTY_LOCAL_SEGMENT
from uv_upx.services.local_segments.exceptions import NonEmptyLocalSegmentsError
from uv_upx.services.run_uv_related.exceptions import UnresolvedDependencyError

if TYPE_CHECKING:
    import pathlib


# noinspection PyTypeChecker
@safe_with(UnresolvedDependencyError, NonEmptyLocalSegmentsError)
def run_uv_lock(
    workdir: pathlib.Path,
    *,
    upgrade: bool = False,
) -> None:
    # uv lock --upgrade
    command = ["uv", "lock"]
    if upgrade:
        command.append("--upgrade")
    # Note: stderr is captured to detect the local segments error, then shown to the user as uv printed it.
    completed = subprocess.run(  # noqa: S603  # Fixed argv: `uv` and flags built here, no user input.
        command,
        check=False,
        cwd=workdir,
        stderr=subprocess.PIPE,
        text=True,
    )
    _ = sys.stderr.write(completed.stderr)
    try:
        completed.check_returncode()
    except subprocess.CalledProcessError as e:
        if ERROR_TEXT_PART_I_NON_EMPTY_LOCAL_SEGMENT in completed.stderr:
            msg = (
                "Failed to resolve dependencies with 'uv lock' due to non-empty local segments. "
                "Please check your dependency specifications."
            )
            raise NonEmptyLocalSegmentsError(
                msg,
            ) from e

        msg = "Failed to resolve dependencies with 'uv lock'. Please check your dependency specifications."
        raise UnresolvedDependencyError(
            msg,
        ) from e
