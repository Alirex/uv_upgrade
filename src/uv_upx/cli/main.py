import pathlib  # noqa: TC003
from typing import Annotated

import typer

from uv_upx.services.normalize_paths import normalize_and_check_path_to_project_root
from uv_upx.services.run_updater import run_updater

app = typer.Typer(
    pretty_exceptions_enable=False,
)


@app.command()
def run(
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
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show changes without writing file")] = False,
    #
    verbose: Annotated[bool, typer.Option("--verbose", help="Show more output")] = False,
    #
    preserve_original_package_names: Annotated[
        bool,
        typer.Option("--preserve-original-package-names", help="Preserve original package names in pyproject.toml"),
    ] = False,
    #
    no_sync: Annotated[
        bool,
        typer.Option(
            "--no-sync",
            help="Do not run uv-sync. "
            "In case of the complex build process. "
            "But, recommended to run with sync, for better chances for revealing problems.",
        ),
    ] = False,
) -> None:
    """Update pyproject.toml dependencies to latest PyPI releases."""
    path = normalize_and_check_path_to_project_root(project_root_path)

    run_updater(
        project_root_path=path,
        #
        dry_run=dry_run,
        verbose=verbose,
        #
        preserve_original_package_names=preserve_original_package_names,
        #
        no_sync=no_sync,
    )
