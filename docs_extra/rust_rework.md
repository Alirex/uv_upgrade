# Rust rework: state, distribution plan, switch-over

Status (2026-10-25): **ported, not yet shipped.** The Rust implementation lives in `rust/uv_upx/` next to the Python
package and passes the same tests plus parity tests against the Python CLI. PyPI still ships the Python package
until the switch-over checklist below is done. The old branch `features/rust` (one commit `fa7571f`, 2026-02-28) is
superseded by this port and can be deleted; nothing was taken from it (it predated 0.4.5, used tokio and a different
CLI shape).

## What is where

| Path                           | Content                                                                                           |
| ------------------------------ | ------------------------------------------------------------------------------------------------- |
| `Cargo.toml` (root)            | The cargo workspace: one member, `[workspace.lints]` (pedantic clippy, `unsafe_code = "forbid"`)  |
| `rust/uv_upx/`                 | The crate `uv-upx`: library + the two binaries `uv-upx` and `uv-upgrade`                          |
| `rust/uv_upx/src/`             | One module per Python service (`collect`, `dependency/`, `updater`, `uv_runner`, `pyprojects`, …) |
| `rust/uv_upx/tests/cli.rs`     | The CLI and the upgrade flow through the binaries with a fake `uv` (counterparts of the pytest)   |
| `rust/uv_upx/tests/parity.rs`  | Both CLIs on identical fixtures: files, stdout, log lines, exit codes and `uv` calls must match   |
| `rust/uv_upx/tests/snapshots/` | `insta` snapshots of the help texts                                                               |
| `rust/uv_upx/pyproject.toml`   | The maturin project of the wheel (`bindings = "bin"`); not a uv workspace member                  |
| `src/uv_upx/`                  | The Python package, unchanged, still what `uv build` and PyPI ship                                |

A root workspace plus `rust/<crate>` (rather than a crate at the repo root) keeps `cargo` commands working from the
root, keeps Rust sources out of the Python `src/`, and leaves room for a second crate (e.g. a library split) without
moving files.

## Crates (what replaced what)

| Need                               | Crate                                  | Replaces                                                |
| ---------------------------------- | -------------------------------------- | ------------------------------------------------------- |
| Format-preserving `pyproject.toml` | `toml_edit`                            | tomlkit                                                 |
| CLI                                | `clap` (derive), `clap_complete`       | typer (`--install-completion`, `--show-completion` too) |
| Dependency strings                 | `regex` (a port of the Python regexes) | `parse_dependency.py`                                   |
| Workspace member globs             | `glob`                                 | `pathlib.Path.glob`                                     |
| Interactive accept/reject          | `inquire`                              | prompt-toolkit                                          |
| Log lines in Python's format       | `chrono` (timestamps)                  | `logging.basicConfig`                                   |
| Errors                             | `thiserror`                            | safe-result, exceptions                                 |
| Tests                              | `insta`, `tempfile`                    | pytest                                                  |

`pep508_rs` / `pep440_rs` were planned but not used on purpose: they normalize markers and versions on output
(`python_version<'3.11'` would come back as `python_version < '3.11'`), while the tool writes the parts back
verbatim. Byte parity of the resulting files needed the lenient regex parser.

## Parity

Checked by `cargo test --test parity` (needs the venv: `just dev-sync`; skipped with a note without it). 28 runs in
10 scenarios: simple project, `--no-sync`, `--dry-run`, `--verbose`, nothing to upgrade, failing `uv sync`, failing
`uv lock`, the local-segment fallback, `--keep-unconstrained`, `--preserve-original-package-names`, a workspace with
comments, trailing comments, odd whitespace, single quotes, nested groups, workspace sources, extras, markers,
excluded members, the `with_pinned` profile, the helpers command with and without `--only-special-cases`, errors
before the update, `--version`.

Same on both sides:

- the resulting `pyproject.toml` files and `uv.lock` (byte for byte, comments and formatting kept);
- stdout, and the log lines on stderr (`name - LEVEL - message`, the Python logger names kept);
- exit codes: 0 after a success and after a rolled-back failure (as the Python version does), 1 for an error before
  the update (missing `uv.lock`, invalid dependency string), 2 for a usage error;
- the sequence of `uv` calls (`uv lock --upgrade`, `uv sync --all-groups --all-extras --all-packages`, `--frozen`).

Known differences (intended):

- Help text layout: clap's instead of Typer's rich panels; the option names, order and help strings are the same,
  `--help` has no `-h`, `uv-upx upgrade` and `helpers` have no description line (Typer shows none either).
- Error messages before the update: one `Error: …` line instead of a Python traceback; after the update started,
  the rollback log line still quotes the Python exception type (`'<class '…UnresolvedDependencyError'>:…'`).
- A relative `--project` path works (Python's `as_uri()` raises `ValueError` on it).
- The interactive prompt is `inquire`'s select, not prompt-toolkit's; Ctrl-C rolls back instead of leaving the
  files half-written.
- Workspace members are visited in path order (Python iterates a set).
- Timestamps are local time with milliseconds like Python's; the sub-millisecond ordering of identical lines is
  the same.

## Distribution: keep the PyPI name, ship binaries

[maturin](https://www.maturin.rs/bindings#bin) with `bindings = "bin"` builds a wheel that contains the two
executables as scripts and no Python code. `uv tool install uv-upx`, `uvx uv-upx` and `uvx --from uv-upx uv-upgrade`
keep working; `requires-python` drops to `>=3.9` because no interpreter runs.

Verified locally: `just rel-wheel-rust` (= `uvx maturin build --release` in `rust/uv_upx`) gives
`uv_upx-0.5.0-py3-none-manylinux_2_39_x86_64.whl` (2.7 MB; binaries 3.0 MB each, stripped, LTO), and
`uv tool install <wheel>` installs both executables.

Release pipeline (to add at the switch-over, nothing published yet):

1. `maturin generate-ci github --pytest false` as `.github/workflows/release.yml`: wheels for Linux (x86_64,
   aarch64; glibc via the manylinux images, plus musl), macOS (x86_64, arm64) and Windows (x86_64), plus the sdist.
2. Trigger on a tag `v*`; the upload job is a separate `release` environment with a required reviewer, so a tag
   builds and the maintainer approves the upload. PyPI trusted publishing (OIDC) for the project `uv-upx`, no token
   in the repo.
3. The sdist builds from source with cargo (`uv tool install` on an unsupported platform falls back to it).

Alternatives considered: `cargo-dist` (GitHub releases + installers; good for `curl | sh`, but it does not publish to
PyPI, and PyPI is how the users install today) and a thin Python wrapper that downloads the binary (an extra moving
part and a network call at install time).

## Switch-over checklist

Do it in one short-lived branch; each step is a commit.

1. Root `pyproject.toml`: replace `[build-system]` (`uv_build` → `maturin`), set `dynamic = ["version"]`, drop
   `dependencies` and `[project.scripts]` (maturin registers the binaries), keep `readme`, `keywords`, URLs; move
   `[tool.maturin]` in from `rust/uv_upx/pyproject.toml` with `manifest-path = "rust/uv_upx/Cargo.toml"`, then
   delete that file. `uv build` must produce the bin wheel.
2. Bump the minor version in `Cargo.toml` (`[workspace.package]`) and, until step 4, in `pyproject.toml`; the Rust
   test `version_matches_pyproject` keeps them equal (drop that test when the version is only in `Cargo.toml`).
3. Regenerate `docs_extra/cli_help_*.md` from the Rust binaries (`--help` output; the `typer utils docs` hooks go),
   update `README.md` (install section unchanged; "Why not in Rust?" goes) and `docs_extra/dev.md` (setup: rustup;
   release: tag → CI).
4. Remove the Python package: `src/uv_upx/`, the Python dev dependencies and tool config in `pyproject.toml`,
   `uv.lock`, the Python prek hooks (`ruff`, `mypy`, `basedpyright`, `pytest`, `uv-lock`, the help generators), the
   Python CI jobs; keep `prettier`, `shellcheck`, the generic hooks, `mdremotifier`, and the cargo hooks. The parity
   test goes with it (`tests/parity.rs` and the venv lookup); `tests/cli.rs` stays as the behaviour suite.
5. Add the release workflow (above), configure trusted publishing on PyPI, dry-run with `maturin build` on the
   matrix, then tag. **Publishing needs the maintainer's explicit OK** (AGENTS.md).
6. Delete the branch `features/rust`; update `AGENTS.md` (one implementation) and HQ's registry tags.

Until then: a behaviour change lands in both implementations with a parity scenario; `just q-check` runs both test
suites.

## Open items

- Windows: the fake `uv` of the tests is a shell script, so the flow and parity tests are Unix-only (`#[cfg(unix)]`);
  the unit tests and the CLI argument tests run everywhere. A `.cmd` fake, or a tiny Rust fake-uv binary, would
  cover Windows in CI.
- `helpers collect-top-level-dependencies-from-project` prints nothing without `--only-special-cases` in both
  implementations (the Python `filter_dependencies` yields only inside that branch); kept for parity, worth fixing in
  both.
- A failed `uv lock`/`uv sync` is rolled back and still exits 0 (both implementations); a non-zero exit would be
  more useful in scripts. Decide at the switch-over (it is a behaviour change).
- `--install-completion` writes where Typer does (`~/.bash_completions/<name>.sh` + `~/.bashrc`, `~/.zfunc/_<name>`,
  fish completions dir); PowerShell/elvish print the script with `--show-completion` only.
