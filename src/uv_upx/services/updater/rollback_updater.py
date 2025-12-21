import copy
import logging
import pathlib

from pydantic import BaseModel, ConfigDict
from tomlkit import TOMLDocument

from uv_upx.services.get_all_pyprojects import PyProjectsRegistry
from uv_upx.services.run_uv_related import UvSyncMode, run_uv_sync
from uv_upx.services.toml import toml_save


class UvLockWrapper(BaseModel):
    path: pathlib.Path
    data: TOMLDocument

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class RollbackData(BaseModel):
    uv_lock: UvLockWrapper

    py_projects: PyProjectsRegistry

    @classmethod
    def from_parts(
        cls,
        *,
        uv_lock_path: pathlib.Path,
        uv_lock_data: TOMLDocument,
        #
        py_projects: PyProjectsRegistry,
    ) -> RollbackData:
        uv_lock_wrapper = UvLockWrapper(
            path=uv_lock_path,
            data=copy.deepcopy(uv_lock_data),
        )
        return cls(
            uv_lock=uv_lock_wrapper,
            py_projects=copy.deepcopy(py_projects),
        )


def rollback_updater(
    *,
    rollback_data: RollbackData,
    #
    no_sync: bool = False,
) -> None:
    logger = logging.getLogger(__name__)

    toml_save(rollback_data.uv_lock.path, rollback_data.uv_lock.data)
    for py_project in rollback_data.py_projects.items:
        toml_save(py_project.path, py_project.data)

    if not no_sync:
        run_uv_sync(
            workdir=rollback_data.uv_lock.path.parent,
            uv_sync_mode=UvSyncMode.FROZEN,
        )

    logger.info("Rollback completed.")
