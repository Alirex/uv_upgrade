import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathlib


class UnresolvedDependencyError(Exception):
    pass


def run_uv_lock_upgrade(workdir: pathlib.Path) -> None:
    try:
        subprocess.run(
            # uv lock --upgrade
            ["uv", "lock", "--upgrade"],  # noqa: S607
            check=True,
            cwd=workdir,
        )
    except subprocess.CalledProcessError as e:
        msg = "Failed to resolve dependencies with 'uv lock'. Please check your dependency specifications."
        raise UnresolvedDependencyError(
            msg,
        ) from e


def run_uv_lock(workdir: pathlib.Path) -> None:
    try:
        subprocess.run(
            # uv lock
            ["uv", "lock"],  # noqa: S607
            check=True,
            cwd=workdir,
        )
    except subprocess.CalledProcessError as e:
        msg = "Failed to resolve dependencies with 'uv lock'. Please check your dependency specifications."
        raise UnresolvedDependencyError(
            msg,
        ) from e


def run_uv_sync(workdir: pathlib.Path) -> None:
    try:
        subprocess.run(
            # uv sync --all-groups --all-extras --all-packages
            ["uv", "sync", "--all-groups", "--all-extras", "--all-packages"],  # noqa: S607
            check=True,
            cwd=workdir,
        )
    except subprocess.CalledProcessError as e:
        msg = "Failed to sync dependencies with 'uv sync'. Please check your dependency specifications."
        raise UnresolvedDependencyError(
            msg,
        ) from e


def run_uv_sync_upgrade(workdir: pathlib.Path) -> None:
    # Note: Better to use this for new dependencies.
    # Because it uses a better resolver for conflicts.
    try:
        subprocess.run(
            # uv sync --all-groups --all-extras --all-packages --upgrade
            ["uv", "sync", "--all-groups", "--all-extras", "--all-packages", "--upgrade"],  # noqa: S607
            check=True,
            cwd=workdir,
        )
    except subprocess.CalledProcessError as e:
        msg = "Failed to sync dependencies with 'uv sync'. Please check your dependency specifications."
        raise UnresolvedDependencyError(
            msg,
        ) from e


def run_uv_sync_frozen(workdir: pathlib.Path) -> None:
    try:
        subprocess.run(
            # uv sync --all-groups --all-extras --all-packages --frozen
            ["uv", "sync", "--all-groups", "--all-extras", "--all-packages", "--frozen"],  # noqa: S607
            check=True,
            cwd=workdir,
        )
    except subprocess.CalledProcessError as e:
        msg = "Failed to sync dependencies with 'uv sync'. Please check your dependency specifications."
        raise UnresolvedDependencyError(
            msg,
        ) from e
