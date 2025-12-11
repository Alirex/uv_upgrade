from typing import TYPE_CHECKING

from uv_upx.services.run_uv_related import UvSyncMode, run_uv_sync
from uv_upx.services.toml import toml_save

if TYPE_CHECKING:
    import pathlib

    from tomlkit import TOMLDocument

    from uv_upx.services.get_all_pyprojects import PyProjectsRegistry


def rollback_updater(
    *,
    uv_lock_path: pathlib.Path,
    uv_lock_data: TOMLDocument,
    #
    py_projects: PyProjectsRegistry,
    #
    no_sync: bool = False,
) -> None:
    toml_save(uv_lock_path, uv_lock_data)
    for py_project in py_projects.items:
        toml_save(py_project.path, py_project.data)

    if not no_sync:
        run_uv_sync(
            workdir=uv_lock_path.parent,
            uv_sync_mode=UvSyncMode.FROZEN,
        )
