import pathlib  # noqa: TC003
from typing import Annotated

import typer

from uv_upgrade.services.normalize_and_check_path_to_pyproject import normalize_and_check_path_to_project_root
from uv_upgrade.services.run_updater import run_updater

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
) -> None:
    """Update pyproject.toml dependencies to latest PyPI releases."""
    path = normalize_and_check_path_to_project_root(project_root_path)

    run_updater(
        project_root_path=path,
        dry_run=dry_run,
        verbose=verbose,
    )
