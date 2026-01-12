from typing import TYPE_CHECKING

from safe_result import safe_with

from uv_upx.services.local_segments.exceptions import NonEmptyLocalSegmentsError
from uv_upx.services.run_uv_related import UnresolvedDependencyError, run_uv_lock

if TYPE_CHECKING:
    import pathlib


@safe_with(UnresolvedDependencyError, NonEmptyLocalSegmentsError)
def update_lock_file(
    project_root_path: pathlib.Path,
) -> None:
    # Because we want a fast update. Without triggering build for now.
    run_uv_lock(
        workdir=project_root_path,
        upgrade=True,
    ).unwrap()
