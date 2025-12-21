import importlib
import pathlib  # noqa: TC003
from typing import Annotated

import typer

from uv_upx.services.normalize_paths import normalize_and_check_path_to_project_root
from uv_upx.services.updater import run_updater
from uv_upx.services.upgrade_profile import UpgradeProfile

app = typer.Typer(
    pretty_exceptions_enable=False,
    pretty_exceptions_show_locals=False,
)


def version_callback(
    value: bool,  # noqa: FBT001
) -> None:
    if value:
        app_name = "uv-upx"
        version: str = importlib.metadata.version(app_name)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
        typer.echo(f"{app_name} {version}")
        raise typer.Exit


# noinspection PyUnusedLocal
@app.command()
def run(  # noqa: PLR0913
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
    #
    profile: Annotated[
        UpgradeProfile | None,
        typer.Option(
            "--profile",
            help="Which profile to use when upgrading dependencies. (Experimental feature)",
        ),
    ] = None,
    #
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive",
            help="Enable interactive mode for selecting updates. (Experimental feature)",
        ),
    ] = False,
    #
    version: Annotated[  # noqa: ARG001  # pyright: ignore[reportUnusedParameter]
        bool | None,
        typer.Option(
            "--version",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """Update pyproject.toml dependencies to latest compatible versions."""
    run_updater(
        project_root_path=normalize_and_check_path_to_project_root(project_root_path),
        #
        dry_run=dry_run,
        verbose=verbose,
        #
        preserve_original_package_names=preserve_original_package_names,
        #
        no_sync=no_sync,
        #
        interactive=interactive,
        #
        profile=profile or UpgradeProfile.get_default(),
    )
