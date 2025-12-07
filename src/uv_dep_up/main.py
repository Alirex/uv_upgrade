"""Update dependencies in `pyproject.toml` to the latest PyPI versions.

Usage:
  python scripts/update_deps.py [--pyproject PATH] [--dry-run]

Requires either `tomlkit` or `toml` installed to write the TOML file.
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

PYPROJECT_DEFAULT = Path("pyproject.toml")


def load_toml(path: Path):
    try:
        import tomlkit as tk  # type: ignore

        data = tk.parse(path.read_text(encoding="utf-8"))
        return data, "tomlkit", tk
    except Exception:
        try:
            import toml  # type: ignore

            data = toml.loads(path.read_text(encoding="utf-8"))
            return data, "toml", toml
        except Exception:
            print(
                "Please install either `tomlkit` or `toml` to run this script.",
                file=sys.stderr,
            )
            sys.exit(1)


def save_toml(path: Path, data, backend: str, module) -> None:
    text = None
    text = module.dumps(data) if backend == "tomlkit" else module.dumps(data)
    path.write_text(text, encoding="utf-8")


# Simple pattern to capture name+extras and the rest (specifier and markers).
_DEP_RE = re.compile(r"^\s*(?P<name>[A-Za-z0-9_.\-]+(?:\[[^\]]+\])?)(?P<rest>.*)$")


def is_vcs_or_url(dep: str) -> bool:
    s = dep.strip()
    return s.startswith(("git+", "http://", "https://", "file:", "-e ")) or "://" in s


def split_marker(dep: str) -> tuple[str, str | None]:
    # Preserve environment marker (after ;)
    parts = dep.split(";", 1)
    main = parts[0].strip()
    marker = f";{parts[1].strip()}" if len(parts) == 2 else None
    return main, marker


def parse_name_and_extras(main: str) -> str | None:
    m = _DEP_RE.match(main)
    if not m:
        return None
    return m.group("name")


def fetch_latest_version(package: str) -> str | None:
    url = f"https://pypi.org/pypi/{package}/json"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            if resp.status != 200:
                return None
            payload = json.load(resp)
            # `info.version` is usually the latest released version.
            return payload.get("info", {}).get("version")
    except Exception:
        return None


def update_list_deps(
    deps: list[str],
    dry_run: bool = False,
) -> tuple[list[str], dict[str, str]]:
    updated = []
    changes = {}
    for dep in deps:
        orig = dep
        if is_vcs_or_url(dep):
            updated.append(dep)
            continue
        main, marker = split_marker(dep)
        name_with_extras = parse_name_and_extras(main)
        if not name_with_extras:
            updated.append(dep)
            continue
        # Strip extras for PyPI lookup (e.g. "pkg[extra]" -> "pkg")
        pkg_name = name_with_extras.split("[", 1)[0]
        latest = fetch_latest_version(pkg_name)
        if not latest:
            print(
                f"Warning: could not fetch latest for {pkg_name}; leaving '{dep}' unchanged.",
            )
            updated.append(dep)
            continue
        new_spec = f"{name_with_extras}=={latest}"
        if marker:
            new_spec = f"{new_spec} {marker}"
        if new_spec != orig:
            changes[orig] = new_spec
            print(f"{orig} -> {new_spec}")
        updated.append(new_spec if not dry_run else orig)
    return updated, changes


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Update pyproject.toml dependencies to latest PyPI releases.",
    )
    parser.add_argument(
        "--pyproject",
        "-p",
        type=Path,
        default=PYPROJECT_DEFAULT,
        help="Path to pyproject.toml",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without writing file",
    )
    args = parser.parse_args()

    path = args.pyproject
    if not path.exists():
        print(f"pyproject file not found at {path}", file=sys.stderr)
        sys.exit(2)

    data, backend, module = load_toml(path)

    # Locate project.dependencies (list)
    project = data.get("project", {})
    if not isinstance(project, dict):
        print("No [project] table found in pyproject.toml", file=sys.stderr)
        sys.exit(3)

    changed_any = False
    if "dependencies" in project and isinstance(project["dependencies"], list):
        print("Updating [project].dependencies ...")
        new_deps, changes = update_list_deps(
            project["dependencies"],
            dry_run=args.dry_run,
        )
        if changes:
            changed_any = True
            if backend == "tomlkit":
                # tomlkit preserves container types
                project["dependencies"] = type(project["dependencies"])(new_deps)
            else:
                project["dependencies"] = new_deps

    # dependency-groups table
    dep_groups = data.get("dependency-groups", {})
    if isinstance(dep_groups, dict):
        for group_name, group_val in list(dep_groups.items()):
            if isinstance(group_val, list):
                print(f"Updating [dependency-groups].{group_name} ...")
                new_list, changes = update_list_deps(group_val, dry_run=args.dry_run)
                if changes:
                    changed_any = True
                    if backend == "tomlkit":
                        dep_groups[group_name] = type(group_val)(new_list)
                    else:
                        dep_groups[group_name] = new_list

    if not changed_any:
        print("No changes detected.")
        return

    if args.dry_run:
        print("Dry run complete. No file written.")
        return

    # Write back
    try:
        save_toml(path, data, backend, module)
        print(f"Wrote updated dependencies to {path}")
    except Exception as exc:
        print(f"Failed to write {path}: {exc}", file=sys.stderr)
        sys.exit(4)
