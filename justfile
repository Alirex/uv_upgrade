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

# Publish to PyPI; only with the maintainer's OK: `just rel-publish yes` after `just rel-build`.
[group('release')]
rel-publish confirm="no":
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ "{{ confirm }}" != "yes" ]]; then
        echo "Publishing needs the maintainer's OK. Would run: uv publish"
        echo "Rerun with: just rel-publish yes"
        exit 1
    fi
    uv publish
    echo https://pypi.org/project/uv-upx
