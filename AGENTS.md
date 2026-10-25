# uv-upx: instructions for AI agents

`uv-upx` (PyPI; commands `uv-upx` and `uv-upgrade`) is a Typer CLI that upgrades dependency constraints in the
`pyproject.toml` of uv projects and workspaces. Python 3.14, uv, pydantic, tomlkit.

## Layout

- `src/uv_upx/`: the package (`cli/`, `services/`, ...). Tests sit next to the code in `tests/` folders
  (`src/uv_upx/**/tests/`).
- `docs_extra/`: dev notes (`dev.md`: setup, release) and generated CLI help (`cli_help_*.md`).
- `README.md` is the source; `README.remotified.md` (the PyPI readme) is generated from it.
- The `features/rust` branch holds a started Rust rewrite; do not merge it or copy from it unasked. The plan for
  resuming it is in `docs_extra/rust_rework.md`.
- The repo is small and personal: commit to `main` directly, no PRs. Read-only questions need no branch.

## Commands

[just](https://just.systems) is the entry point (`just` lists recipes); the poe tasks in `pyproject.toml` still work.

- `just q-check`: the full gate (`prek run --all-files` with `SKIP=pre-commit-update`, then pytest, basedpyright, mypy,
  each once). It must pass before committing.
- `just q-fast`: prek hooks only (cheap fixers and linters; basedpyright is a pre-push hook), for the edit loop.
  `just q-test`: pytest. `just q-lint`: `ruff check --fix --unsafe-fixes` by hand; review `git diff` after.
- Hooks: shellcheck (`shellcheck-py`, `.shellcheckrc` `enable=all`), markdownlint (`.markdownlint.yaml`), format-justfile.
  `just dev-hooks` installs the commit and push hooks.
- `just dev-sync`: `uv sync --all-packages`. `just rel-build`: clean `dist/` and build.
- Prek fixers rewrite files; run the gate again until it passes.
- Never commit the version bump of the `pre-commit-update` hook unasked.

## Code rules

- Fully typed; basedpyright `all`, mypy `strict` + the pydantic plugin, ruff `ALL`. Fix the warning, do not silence it: fix the code,
  make the types stricter (validate at the boundary into a pydantic model), restructure, and only then suppress one
  line with the rule code and a reason. Turning a rule off in the config needs a reason comment.
- Every behaviour change comes with a test in the nearest `tests/` folder.
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
