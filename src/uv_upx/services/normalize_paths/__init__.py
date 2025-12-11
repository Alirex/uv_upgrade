import pathlib
from typing import Final

__all__ = [
    "NAME_OF_PYPROJECT_FILE",
    "NAME_OF_UV_LOCK_FILE",
    "get_and_check_path_to_pyproject",
    "get_and_check_path_to_uv_lock",
    "normalize_and_check_path_to_project_root",
]


NAME_OF_PYPROJECT_FILE: Final[str] = "pyproject.toml"
NAME_OF_UV_LOCK_FILE: Final[str] = "uv.lock"


def normalize_and_check_path_to_project_root(path: pathlib.Path | None) -> pathlib.Path:
    if path is None:
        path = pathlib.Path.cwd()

    if not path.is_dir():
        msg = f"Path {path} is not a directory."
        raise NotADirectoryError(msg)

    if not path.exists():
        msg = f"Path {path} does not exist."
        raise FileNotFoundError(msg)

    return path


def get_and_check_path_to_pyproject(path: pathlib.Path) -> pathlib.Path:
    path = path / NAME_OF_PYPROJECT_FILE

    if not path.exists():
        msg = f"Path {path} does not exist."
        raise FileNotFoundError(msg)

    return path


def get_and_check_path_to_uv_lock(path: pathlib.Path) -> pathlib.Path:
    path = path / NAME_OF_UV_LOCK_FILE

    if not path.exists():
        msg = f"Path {path} does not exist."
        raise FileNotFoundError(msg)

    return path
