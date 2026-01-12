import subprocess
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
    try:
        subprocess.run(  # noqa: S603
            # uv lock --upgrade
            command,
            check=True,
            cwd=workdir,
        )
    except subprocess.CalledProcessError as e:
        if e.stderr and ERROR_TEXT_PART_I_NON_EMPTY_LOCAL_SEGMENT in e.stderr.decode():
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
