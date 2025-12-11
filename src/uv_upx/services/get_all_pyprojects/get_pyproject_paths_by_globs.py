import logging
from typing import TYPE_CHECKING

from uv_upx.services.normalize_paths import NAME_OF_PYPROJECT_FILE

if TYPE_CHECKING:
    import pathlib


def get_pyproject_paths_by_globs(
    base_path: pathlib.Path,
    patterns: list[str],
) -> set[pathlib.Path]:
    paths: set[pathlib.Path] = set()

    logger = logging.getLogger(__name__)

    for pattern in patterns:
        for path in base_path.glob(pattern):
            if path.is_file():
                if path.name == NAME_OF_PYPROJECT_FILE:
                    paths.add(path)
            elif path.is_dir():
                path_candidate = path / NAME_OF_PYPROJECT_FILE
                if path_candidate.exists():
                    paths.add(path_candidate)
            else:
                # sourcery skip: remove-redundant-pass
                # Explicit skip for other cases
                logger.warning(f"Skipping {path.as_uri()}: not a file or directory.")

    return paths
