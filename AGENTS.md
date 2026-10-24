# uv-upx: instructions for AI agents

`uv-upx` (PyPI; commands `uv-upx` and `uv-upgrade`) upgrades dependency constraints in the `pyproject.toml` of uv
projects and workspaces. Two implementations live side by side until the switch-over: the Typer CLI in `src/uv_upx/`
(Python 3.14, pydantic, tomlkit; what PyPI ships) and its port in `rust/uv_upx/` (clap, toml_edit; the same
commands, flags, log lines and file edits).

## Layout

- `src/uv_upx/`: the package (`cli/`, `services/`, ...). Tests sit next to the code in `tests/` folders
  (`src/uv_upx/**/tests/`).
- `docs_extra/`: dev notes (`dev.md`: setup, release) and generated CLI help (`cli_help_*.md`).
- `README.md` is the source; `README.remotified.md` (the PyPI readme) is generated from it.
- `rust/uv_upx/`: the Rust crate (root `Cargo.toml` is the workspace). Unit tests sit in the modules, the CLI and
  parity tests in `rust/uv_upx/tests/` (`parity.rs` runs both CLIs on the same fixtures and needs the venv).
  `rust/uv_upx/pyproject.toml` is the maturin wheel of the binaries, not a uv workspace member. State, distribution
  plan and switch-over checklist: `docs_extra/rust_rework.md`. The old `features/rust` branch is superseded.
- The repo is small and personal: commit to `main` directly, no PRs. Read-only questions need no branch.

## Commands

[just](https://just.systems) is the entry point (`just` lists recipes); the poe tasks in `pyproject.toml` still work.

- `just q-check`: the full gate (`prek run --all-files` incl. `cargo fmt` and `cargo clippy`, pytest, basedpyright,
  mypy, `cargo test`). It must pass before committing.
- `just q-fast`: prek hooks only, for the edit loop. `just q-test`: pytest. `just q-test-rust`: cargo test.
- `just dev-sync`: `uv sync --all-packages`. `just rel-build`: clean `dist/` and build.
- Prek fixers rewrite files; run the gate again until it passes.
- Never commit the version bump of the `pre-commit-update` hook unasked.

## Code rules

- Fully typed; basedpyright `all`, mypy `strict` + the pydantic plugin, ruff `ALL`. Fix the warning, do not silence it: fix the code,
  make the types stricter (validate at the boundary into a pydantic model), restructure, and only then suppress one
  line with the rule code and a reason. Turning a rule off in the config needs a reason comment.
- Rust: `clippy::pedantic` warns and warnings fail (`-D warnings`), `unsafe_code` is forbidden, `unwrap`/`expect`
  outside tests and every `#[expect]` need a reason. Same spirit: fix the code before suppressing.
- Every behaviour change comes with a test in the nearest `tests/` folder. While both implementations exist, a
  behaviour change lands in both, with the parity test covering it.
- When the CLI changes (options, help text), run the gate: the prek hooks regenerate `docs_extra/cli_help_*.md` and
  `README.remotified.md`; commit them. Update `README.md` by hand when usage changes.
- Do not edit generated files by hand.

## Release

Steps are in `docs_extra/dev.md` ("Bump, Build and Publish"): `uv version --bump patch`, `uv sync --all-packages`,
`just rel-build`, then `uv publish`. **Publish to PyPI only with the maintainer's explicit OK**; `just rel-publish`
refuses without the argument `yes`. Never bump the version unasked.

## Reasoning

Shared best practices and the reasons behind these rules: <https://github.com/evocaslab/hq/tree/main/practices>
(`quality-gate.md`, `lint-strictness.md`, `just-task-runner.md`, `gitignore-and-ide.md`).
