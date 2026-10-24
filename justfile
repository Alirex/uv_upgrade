# uv-upx recipes. Run `just` for the list. Prefixes: q- quality, dev- setup, rel- release. Rust needs cargo (rustup).

set shell := ["bash", "-euo", "pipefail", "-c"]

[private]
default:
    @just --list

# Full gate: prek hooks (incl. cargo fmt and clippy), pytest, basedpyright, mypy, cargo test. Run again if fixers changed files.
[group('quality')]
q-check:
    prek run --all-files
    uv run pytest
    uv run basedpyright
    uv run mypy src
    cargo test

# Fast loop: prek hooks only (formatters, ruff, generated docs).
[group('quality')]
q-fast:
    prek run --all-files

# Run the Python tests.
[group('quality')]
q-test *args:
    uv run pytest {{ args }}

# Run the Rust tests (rust/uv_upx); the parity tests need the venv (`just dev-sync`), else they are skipped.
[group('quality')]
q-test-rust *args:
    cargo test {{ args }}

# Create or update the venv with all workspace packages.
[group('dev')]
dev-sync:
    uv sync --all-packages

# Install the git hooks (once per clone).
[group('dev')]
dev-hooks:
    prek install

# Clean dist (keeps dist/.gitignore) and build the package.
[group('release')]
rel-build:
    mkdir -p dist
    find dist -type f -not -name '.gitignore' -delete
    uv build

# Build the wheel of the Rust binaries into target/wheels (maturin, not published; see docs_extra/rust_rework.md).
[group('release')]
rel-wheel-rust:
    cd rust/uv_upx && uvx maturin build --release --out ../../target/wheels

# Publish to PyPI; only with the maintainer's OK: `just rel-publish yes` after `just rel-build`.
[group('release')]
rel-publish confirm="no":
    #!/usr/bin/env bash
    set -euo pipefail
    if [ "{{ confirm }}" != "yes" ]; then
        echo "Publishing needs the maintainer's OK. Would run: uv publish"
        echo "Rerun with: just rel-publish yes"
        exit 1
    fi
    uv publish
    echo https://pypi.org/project/uv-upx
