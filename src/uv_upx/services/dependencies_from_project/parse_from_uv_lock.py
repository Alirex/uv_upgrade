from typing import TYPE_CHECKING

from uv_upx.services.dependencies_from_project.parse_from_uv_lock_file import parse_from_uv_lock_file
from uv_upx.services.normalize_paths import get_and_check_path_to_uv_lock

if TYPE_CHECKING:
    import pathlib

    from uv_upx.services.dependencies_from_project.models import DependenciesRegistry


def parse_from_uv_lock(
    workdir: pathlib.Path,
) -> DependenciesRegistry:
    return parse_from_uv_lock_file(
        content=get_and_check_path_to_uv_lock(
            workdir,
        ).read_text(),
    )
