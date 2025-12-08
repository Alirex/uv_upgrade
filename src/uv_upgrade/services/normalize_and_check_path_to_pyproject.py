import pathlib
from typing import Final

NAME_OF_PYPROJECT_FILE: Final[str] = "pyproject.toml"


def normalize_and_check_path_to_pyproject(path: pathlib.Path | None) -> pathlib.Path:
    if path is None:
        path = pathlib.Path.cwd() / NAME_OF_PYPROJECT_FILE
    if path.is_dir():
        return path / NAME_OF_PYPROJECT_FILE

    if not path.exists():
        msg = f"Path {path} does not exist."
        raise FileNotFoundError(msg)

    return path
