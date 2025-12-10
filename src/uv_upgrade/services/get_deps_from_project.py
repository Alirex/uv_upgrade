import subprocess
from typing import TYPE_CHECKING, NewType

from uv_upgrade.services.normalize_and_check_path_to_pyproject import get_and_check_path_to_uv_lock
from uv_upgrade.services.save_load_toml import load_toml

if TYPE_CHECKING:
    import pathlib

DependencyName = NewType("DependencyName", str)
Version = NewType("Version", str)

type DependenciesRegistry = dict[DependencyName, Version]


def parse_from_pip(
    workdir: pathlib.Path,
) -> DependenciesRegistry:
    data = subprocess.run(
        # uv pip list --outdated
        ["uv", "pip", "list", "--outdated"],  # noqa: S607
        check=True,
        cwd=workdir,
        capture_output=True,
        text=True,
    )

    # Note: It doesn't provide all necessary dependencies.

    # Example output:
    # Package        Version Latest Type
    # -------------- ------- ------ -----
    # anyio          4.11.0  4.12.0 wheel
    # basedpyright   1.34.0  1.35.0 wheel
    # beautifulsoup4 4.14.2  4.14.3 wheel

    dependencies: DependenciesRegistry = {}
    # Note: skip the header line
    for line in data.stdout.splitlines()[2:]:
        package, _current_version, latest, _type = line.split()
        dependencies[DependencyName(package)] = Version(latest)

    return dependencies


def parse_from_uv_tree(
    workdir: pathlib.Path,
) -> DependenciesRegistry:
    # Note: use this because it has better checks for outdated.
    # For example, `uv pip list --outdated` may miss some packages.
    # But we need extra parsing.

    data = subprocess.run(
        # uv tree --outdated --depth 1 --color never
        [  # noqa: S607
            "uv",
            "tree",
            "--outdated",
            "--depth",
            "1",
            "--color",
            "never",
        ],
        check=True,
        cwd=workdir,
        capture_output=True,
        text=True,
    )

    # Example output:
    # Resolved 129 packages in 0.61ms
    # python-lab v0.1.0
    # ├── jupyter v1.0.0 (latest: v1.1.1)
    # ├── matplotlib v3.10.7
    # ├── pydantic v2.12.5
    # └── pytest v9.0.2 (group: dev)

    # Parse

    dependencies: DependenciesRegistry = {}
    for line in data.stdout.splitlines():
        line = line.strip()  # noqa: PLW2901
        if not line:
            continue

        if line[0].isalpha():
            # Skip the root package line
            continue

        parts = line.split(maxsplit=3)
        # Skip decorative prefix
        parts.pop(0)

        dependency_name = DependencyName(parts.pop(0))

        # Get version
        version_candidate = parts.pop(0)

        if len(parts) == 1:
            version_parts = parts.pop(0).split(") (")

            # Check another version with the "latest:" marker
            for part in version_parts:
                part = part.strip("(").rstrip(")")  # noqa: PLW2901

                sub_parts = part.split(":", 1)

                if len(sub_parts) == 2 and sub_parts[0] == "latest":  # noqa: PLR2004
                    version_candidate = sub_parts[1]

        elif len(parts) > 1:
            msg = f"Unexpected line format: {line}"
            raise ValueError(msg)

        # Strip "v" prefix
        version_candidate = version_candidate.strip().lstrip("v")

        dependencies[dependency_name] = Version(version_candidate)

    return dependencies


def parse_from_uv_lock(
    workdir: pathlib.Path,
) -> DependenciesRegistry:
    uv_lock_path = get_and_check_path_to_uv_lock(workdir)

    data = load_toml(uv_lock_path)

    dependencies: DependenciesRegistry = {}
    for package in data.get("package", []):  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        dependencies[DependencyName(package["name"])] = Version(package["version"])  # pyright: ignore[reportUnknownArgumentType] # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]

    return dependencies


def get_deps_from_project(
    workdir: pathlib.Path,
) -> DependenciesRegistry:
    """Get dependencies info."""
    return parse_from_uv_lock(workdir=workdir)
