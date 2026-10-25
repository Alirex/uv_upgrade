# uv-upx recipes. Run `just` for the list. Prefixes: q- quality, dev- setup, rel- release.

set shell := ["bash", "-euo", "pipefail", "-c"]

[private]
default:
    @just --list

# Full gate: prek hooks, pytest, basedpyright, mypy (each once). Run again if fixers changed files.
[group('quality')]
q-check:
    SKIP=pre-commit-update prek run --all-files
    uv run pytest
    uv run basedpyright
    uv run mypy src

# Fast loop: prek hooks only (formatters, ruff, generated docs).
[group('quality')]
q-fast:
    SKIP=pre-commit-update prek run --all-files

# Ruff with unsafe fixes, by hand. Review `git diff` after.
[group('quality')]
q-lint:
    uv run ruff check --fix --unsafe-fixes

# Scan the whole git history for leaked secrets (gitleaks; monthly and when adopting).
[group('quality')]
q-secrets:
    prek run gitleaks-history --hook-stage manual --all-files

# Run the tests.
[group('quality')]
q-test *args:
    uv run pytest {{ args }}

# Create or update the venv with all workspace packages.
[group('dev')]
dev-sync:
    uv sync --all-packages

# Install the git hooks, commit and push (once per clone).
[group('dev')]
dev-hooks:
    prek install

# Clean dist (keeps dist/.gitignore) and build the package.
[group('release')]
rel-build:
    mkdir -p dist
    find dist -type f -not -name '.gitignore' -delete
    uv build

# Fail unless the tag (default: `v<version>`) equals the pyproject version and the changelog has its section.
[group('release')]
rel-check tag="":
    #!/usr/bin/env bash
    set -euo pipefail
    version="$(uv version --short)"
    tag="{{ tag }}"
    tag="${tag:-v$version}"
    if [[ "$tag" != "v$version" ]]; then
        echo "Tag $tag differs from the pyproject version v$version" >&2
        exit 1
    fi
    if ! grep -qF "## [$version]" CHANGELOG.md; then
        echo "CHANGELOG.md has no section '## [$version]'" >&2
        exit 1
    fi
    echo "OK: $tag"

# Print the changelog section of a version (the GitHub release notes).
[group('release')]
rel-notes version:
    @awk -v v="{{ version }}" '/^## / { on = index($0, "## [" v "]") == 1; next } on' CHANGELOG.md

# Tag the current main commit `v<version>` and push the tag: the release workflow publishes it.
[group('release')]
rel-tag:
    #!/usr/bin/env bash
    set -euo pipefail
    [[ "$(git branch --show-current)" == main ]] || { echo "Not on main" >&2; exit 1; }
    [[ -z "$(git status --porcelain)" ]] || { echo "Dirty tree" >&2; exit 1; }
    git fetch origin main --tags
    [[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || { echo "main differs from origin/main" >&2; exit 1; }
    just rel-check
    tag="v$(uv version --short)"
    if git rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
        echo "$tag exists" >&2
        exit 1
    fi
    just q-check
    git tag -a "$tag" -m "$tag"
    git push origin "$tag"
    echo "Pushed $tag; watch: gh run list -R Alirex/uv_upgrade --workflow release.yml"
