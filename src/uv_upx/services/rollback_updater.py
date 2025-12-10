from typing import TYPE_CHECKING

from uv_upx.services.run_uv_lock import run_uv_sync_frozen
from uv_upx.services.save_load_toml import save_toml

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
) -> None:
    save_toml(uv_lock_path, uv_lock_data)
    for py_project in py_projects.items:
        save_toml(py_project.path, py_project.data)

    run_uv_sync_frozen(workdir=uv_lock_path.parent)
