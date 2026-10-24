# Rust rework: design note

Status (2026-10-25): planned, not started on `main`. The branch `features/rust` (one commit `fa7571f` "temp",
2026-02-28) holds a first cut: a cargo workspace with `rust/uv_upx_r` (clap args, tracing logging, package-name
normalization, `uv lock` / `uv sync` runners, line-based TOML helpers, the binaries `uv-upx` and `uv-upgrade`) and
the Python package removed (its dev notes moved to `docs_extra/dev_python.md`). Do not merge or copy from it unasked
(AGENTS.md); this note says how to resume.

## Goal

Same tool, same name, no Python at runtime: `uv tool install uv-upx` and `uvx uv-upx` keep working, the CLI surface
stays as documented in `docs_extra/cli_help_*.md`, and the behaviour stays as covered by the Python tests.

## Do not start from the branch

`git merge-tree main features/rust` conflicts in 12 files: the branch predates 0.4.5 and deletes Python files that
`main` changed since (#5 `--version`, #6 workspace members, `--keep-unconstrained`, the typed TOML access, the tests).
Resume from `main` instead and take the Rust files over:

```shell
git switch -c feat/rust main
git checkout fa7571f -- Cargo.toml Cargo.lock rust/
```

Keep the Python package in place until the Rust binary passes the same tests (below); only then remove it.

## Crates

| Need                                                        | Crate                                                            | Replaces                                       |
| ----------------------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------- |
| Format-preserving `pyproject.toml` edits                    | `toml_edit` (already in the branch)                              | tomlkit; the branch's `change_content_of_line` |
| Dependency strings (`name[extra]>=1; marker`)               | `pep508_rs` (astral)                                             | the regex parser `parse_dependency.py`         |
| Versions and specifiers (`>=`, `==`, `===`, local segments) | `pep440_rs` (astral)                                             | string compares, `local_segments`              |
| `uv.lock` reading                                           | `toml` + `serde` (`[[package]]` name and version only)           | `parse_from_uv_lock_file.py`                   |
| Workspace member globs                                      | `glob`                                                           | `get_pyproject_paths_by_globs.py`              |
| CLI, completion, help as Markdown                           | `clap`, `clap_complete_command`, `clap-markdown` (in the branch) | typer, `typer utils docs`                      |
| Interactive accept/reject                                   | `inquire` (in the branch)                                        | prompt-toolkit                                 |
| Errors                                                      | `thiserror` for the library, `anyhow` in the binaries            | safe-result                                    |

`tokio` and `async-process` in the branch are not needed: the tool runs two or three `uv` processes one after the
other; use `std::process::Command`.

## Packaging: keep the PyPI name

Build the wheels with [maturin](https://www.maturin.rs/bindings#bin) and `bindings = "bin"` in `pyproject.toml`:
the wheel ships the two binaries as scripts, so `uv tool install uv-upx`, `uvx uv-upx` and `uvx --from uv-upx
uv-upgrade` keep working with no Python code inside. Publish from CI (`maturin generate-ci github`) for Linux
(x86_64, aarch64, musl), macOS (x86_64, arm64) and Windows; a tag triggers the build, the upload stays a manual
approval step (trusted publishing on PyPI, no token in the repo).

## Tests first

Port the Python tests as data before porting the code:

- `src/uv_upx/tests/test_updater.py` and `src/uv_upx/services/updater/tests/test_run_updater.py` already describe the
  flow as `pyproject.toml` + `uv.lock` before/after pairs and the expected `uv` commands. Move them to
  `tests/fixtures/<case>/{pyproject.toml,uv.lock,uv.lock.after,expected/...}` with a small manifest (options, expected
  changes).
- A fake `uv` on `PATH` (a shell or Rust test binary) that records its arguments and copies `uv.lock.after` into
  place, like `fake_uv.py` does by monkeypatching `subprocess.run`.
- Run the fixtures against both implementations (`pytest` and `cargo test`) until the Rust one passes them all.
- The parser unit tests (`test_parse_dependency.py`, `test_version_constraints.py`, `test_update_dependency.py`,
  `test_package_name_normalization.py`) become `rstest` cases.

## Behaviour that must survive

- Only `>=`-style constraints move; `==` only with `--profile with_pinned` (never `===`); other operators are left.
- Dependencies without a constraint get `>=<locked version>` unless `--keep-unconstrained` (#6).
- `{ workspace = true }` sources (root and member `[tool.uv.sources]`) are skipped (#6); nested `include-group`
  entries are skipped.
- Rollback of `pyproject.toml` and `uv.lock` on any failure and on "no changes"; `--dry-run` always rolls back;
  `--no-sync` relocks with `uv lock` instead of `uv sync`.
- The local-segment fallback: when `uv lock` fails on `+local` versions, pin them with `==` and retry.
- Comments and formatting of `pyproject.toml` stay (`toml_edit`).
- `--version` on both binaries (#5).

## Order of work

1. `feat/rust` from `main`, Rust files taken over, `cargo build` green, CI job `cargo test` added.
2. Fixtures and the fake `uv`; pytest runs them (replacing the inline strings).
3. Parser with `pep508_rs`/`pep440_rs`; parser fixtures pass.
4. Updater flow; all fixtures pass; `cargo clippy -- -D warnings` and `cargo fmt --check` join the gate.
5. maturin packaging; `uv tool install .` gives working `uv-upx` and `uv-upgrade`.
6. Remove the Python package, regenerate the CLI help, bump the minor version, release from CI.
