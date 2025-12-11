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
    only_special_cases: Annotated[
        bool,
        typer.Option(
            "--only-special-cases",
            help="Collect only complex and unhandled dependencies",
        ),
    ] = False,
    preserve_original_package_names: Annotated[
        bool,
        typer.Option("--preserve-original-package-names", help="Preserve original package names in pyproject.toml"),
    ] = False,
) -> None:
    """Collect top-level dependencies from the project."""
    collect_top_level_dependencies(
        project_root_path=normalize_and_check_path_to_project_root(project_root_path),
        #
        only_special_cases=only_special_cases,
        #
        preserve_original_package_names=preserve_original_package_names,
    )
