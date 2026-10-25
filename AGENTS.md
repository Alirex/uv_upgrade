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
- `just q-secrets`: gitleaks over the whole history (the commit hook scans staged changes); a real hit is rotated,
  never allowlisted.
- `just dev-sync`: `uv sync --all-packages`. `just rel-build`: clean `dist/` and build.
  `just rel-check`, `just rel-notes`, `just rel-tag`: release.
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

Details in `docs_extra/dev.md` ("Release"). Releases are tag-triggered: `.github/workflows/release.yml` publishes to
PyPI by trusted publishing and creates the GitHub release; there are no local credentials, never `uv publish`.

- The maintainer has allowed releasing when there are user-visible changes since the last tag (SemVer: feature or
  breaking = minor, fix = patch; tooling-only changes are no release). Update `CHANGELOG.md` with every
  user-visible change.
- Bump with `uv version --bump …` and `just dev-sync`, turn `Unreleased` into the new section, land it, wait for green
  CI on `main`, then `just rel-tag` (`just rel-check` fails when the tag differs from the version or the changelog
  has no section).
- Actions are pinned by full SHA with a `# vX.Y.Z` comment; zizmor and Dependabot (7-day cooldown) keep them honest.
- `uv` has `exclude-newer = "7 days"`: a dependency floor must not be younger than a week.

## Reasoning

Shared best practices and the reasons behind these rules: <https://github.com/evocaslab/hq/tree/main/practices>
(`quality-gate.md`, `lint-strictness.md`, `just-task-runner.md`, `gitignore-and-ide.md`,
`releases-and-versions.md`, `supply-chain-security.md`).
