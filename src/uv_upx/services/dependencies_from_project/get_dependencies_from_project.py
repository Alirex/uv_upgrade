from typing import TYPE_CHECKING

from .parse_from_uv_lock import parse_from_uv_lock

if TYPE_CHECKING:
    import pathlib

    from . import DependenciesRegistry


def get_dependencies_from_project(
    workdir: pathlib.Path,
) -> DependenciesRegistry:
    """Get dependencies info.

    Concrete implementation can be changed.
    """
    return parse_from_uv_lock(workdir=workdir)
