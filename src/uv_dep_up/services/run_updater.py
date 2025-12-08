import logging
from typing import TYPE_CHECKING

from uv_dep_up.services.get_deps_by_venv import get_deps_by_venv
from uv_dep_up.services.handle_groups import handle_dependency_groups, handle_main_dependency_group
from uv_dep_up.services.run_uv_lock import run_uv_lock
from uv_dep_up.services.save_load_toml import load_toml, save_toml

if TYPE_CHECKING:
    import pathlib


def run_updater(
    *,
    path_to_pyproject: pathlib.Path,
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    logger = logging.getLogger(__name__)

    data = load_toml(path_to_pyproject)

    new_deps = get_deps_by_venv(workdir=path_to_pyproject.parent)

    if verbose:
        logger.info("Dependencies info found:")
        for dep, latest in new_deps.items():
            logger.info(f"  {dep}: {latest}")

    if not new_deps:
        logger.info("No outdated dependencies found.")
        return

    changed_any = handle_main_dependency_group(
        data=data,
        new_deps=new_deps,
        verbose=verbose,
    )

    changed_any = changed_any or handle_dependency_groups(
        data=data,
        new_deps=new_deps,
        verbose=verbose,
    )

    if not changed_any:
        logger.info("No dependencies were updated.")
        return

    if dry_run:
        logger.info("Dry run mode; not writing changes.")
        return

    save_toml(path_to_pyproject, data)
    logger.info(f"Wrote updated dependencies to {path_to_pyproject.as_uri()}")

    run_uv_lock(workdir=path_to_pyproject.parent)
    logger.info("Updated dependencies successfully.")
