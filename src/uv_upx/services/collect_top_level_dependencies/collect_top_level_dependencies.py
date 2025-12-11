import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathlib


def collect_top_level_dependencies(
    *,
    project_root_path: pathlib.Path,  # noqa: ARG001
    only_complex_and_unhandled: bool = False,  # noqa: ARG001
) -> None:
    logger = logging.getLogger(__name__)

    logger.info("Collecting top level dependencies...")
