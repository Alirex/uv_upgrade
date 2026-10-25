# Dev

## Uv install or update

<https://docs.astral.sh/uv/getting-started/installation/>

```bash
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh;
else
    uv self update;
fi

uv --version
```

## Ruff install or update

<https://docs.astral.sh/ruff/installation/>

```bash
if ! command -v ruff &> /dev/null; then
    uv tool install ruff
else
    uv tool upgrade ruff
fi

ruff --version
```

## Install prek for pre-commit hooks

Needed for automatic linting.

```shell
if ! command -v prek &> /dev/null; then
    curl --proto '=https' --tlsv1.2 -LsSf https://github.com/j178/prek/releases/download/v0.2.19/prek-installer.sh | sh &&\
    prek self update
else
    prek self update
fi

prek --version
```

Note: Run with self-update for installing the latest version of prek. Maybe they will provide a better script later.

## Task runner

[just](https://just.systems) is the entry point: `just` lists the recipes. The poe tasks in `pyproject.toml` still work.

| Recipe                 | What it does                                                                                     |
| ---------------------- | ------------------------------------------------------------------------------------------------ |
| `just dev-sync`        | `uv sync --all-packages`                                                                         |
| `just dev-hooks`       | `prek install`                                                                                   |
| `just q-check`         | full gate: prek hooks, pytest, basedpyright, mypy                                                |
| `just q-lint`          | ruff with unsafe fixes, by hand (review `git diff`)                                              |
| `just q-fast`          | prek hooks only                                                                                  |
| `just q-test`          | pytest                                                                                           |
| `just rel-build`       | clean `dist` (except `.gitignore`) and `uv build`                                                |
| `just rel-check [tag]` | fails unless the tag (default `v<version>`) equals the version and the changelog has its section |
| `just rel-notes <ver>` | prints that version's changelog section (the GitHub release notes)                               |
| `just rel-tag`         | checks, runs the gate, tags `v<version>` on `main` and pushes the tag                            |

## Create venv

```bash
just dev-sync
```

or `uv sync --all-packages`.

## Register pre-commit hooks

Make this after cloning the repository.

```shell
prek install
```

or, if you have pre-commit hooks installed before prek:

```shell
prek install --overwrite
```

Make this each time after cloning the repository.

Don't need to do it after changing the hooks, commit or pull.

## Run pre-commit hooks

If needed, run them manually.

```shell
just q-fast
```

(`prek run --all-files`). `just q-check` also runs pytest, basedpyright and mypy. Useful after changing the hooks. Or just to check if everything is fine.

## Update dependencies

### Install/Update updater

```shell
if ! command -v uv-upx &> /dev/null; then
    uv tool install uv-upx
else
    uv tool upgrade uv-upx
fi

uv-upgrade --version
```

### Update dependencies (before a release)

```shell
cd $(git rev-parse --show-toplevel) &&\
uv-upgrade
```

## Install app system-wide in Development mode

For system-wide usage during development, run this command from the repository directory:

```shell
cd $(git rev-parse --show-toplevel) &&\
uv tool install --editable .
```

## Release (tag-triggered)

Pushing a tag `vX.Y.Z` runs `.github/workflows/release.yml`: it checks the tag against the version, runs the tests,
builds, publishes to PyPI with trusted publishing (no token; job `environment: release`) and creates the GitHub
release from the changelog section. There are no local PyPI credentials: do not run `uv publish`.

1. Update dependencies (see above), land the user-visible changes with their `CHANGELOG.md` lines under `Unreleased`.
2. `uv version --bump minor` (or `patch`), `just dev-sync`; rename `Unreleased` to `[X.Y.Z] - date` in
   `CHANGELOG.md`, add a fresh `Unreleased` and the compare links; `just q-check`; commit and push to `main`.
3. Wait for green CI on `main`, then `just rel-tag`.
4. Watch `gh run list -R Alirex/uv_upgrade --workflow release.yml`; check <https://pypi.org/project/uv-upx>.

One-time setup (PyPI, by the maintainer): trusted publisher for project `uv-upx`: owner `Alirex`, repository
`uv_upgrade`, workflow `release.yml`, environment `release`. Until it exists the `publish` job fails; after adding it,
`gh run rerun <run-id> -R Alirex/uv_upgrade --failed`.

`README.remotified.md` (the PyPI readme, `readme` in `pyproject.toml`) is generated from `README.md` by the
`mdremotifier` prek hook, which `just q-check` and CI run with `--all-files`; commit it with README changes.
