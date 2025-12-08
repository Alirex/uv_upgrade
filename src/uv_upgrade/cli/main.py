import pathlib  # noqa: TC003
from typing import Annotated

import typer

from uv_upgrade.services.normalize_and_check_path_to_pyproject import normalize_and_check_path_to_pyproject
from uv_upgrade.services.run_updater import run_updater

app = typer.Typer(
    pretty_exceptions_enable=False,
)


@app.command()
def run(
    *,
    pyproject: Annotated[
        pathlib.Path | None,
        typer.Option(
            "--pyproject",
            "-p",
            help="Path to pyproject.toml or to folder containing it. Use current working directory if not specified.",
        ),
    ] = None,
    #
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show changes without writing file")] = False,
    #
    verbose: Annotated[bool, typer.Option("--verbose", help="Show more output")] = False,
) -> None:
    """Update pyproject.toml dependencies to latest PyPI releases."""
    path = normalize_and_check_path_to_pyproject(pyproject)

    run_updater(
        path_to_pyproject=path,
        dry_run=dry_run,
        verbose=verbose,
    )
