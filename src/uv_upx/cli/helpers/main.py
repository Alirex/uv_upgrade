import pathlib  # noqa: TC003
from typing import Annotated

import typer

from uv_upx.services.collect_top_level_dependencies.collect_top_level_dependencies import collect_top_level_dependencies
from uv_upx.services.normalize_paths import normalize_and_check_path_to_project_root

app = typer.Typer()


@app.command()
def collect_top_level_dependencies_from_project(
    *,
    project_root_path: Annotated[
        pathlib.Path | None,
        typer.Option(
            "--project",
            "-p",
            help="Path to project root directory. Use current working directory if not specified.",
        ),
    ] = None,
    #
    only_complex_and_unhandled: Annotated[
        bool,
        typer.Option("--only-complex-and-unhandled", help="Collect only complex and unhandled dependencies"),
    ] = False,
) -> None:
    """Collect top-level dependencies from the project."""
    collect_top_level_dependencies(
        project_root_path=normalize_and_check_path_to_project_root(project_root_path),
        #
        only_complex_and_unhandled=only_complex_and_unhandled,
    )
