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

| Recipe                 | What it does                                                |
| ---------------------- | ----------------------------------------------------------- |
| `just dev-sync`        | `uv sync --all-packages`                                    |
| `just dev-hooks`       | `prek install`                                              |
| `just q-check`         | full gate: prek hooks, pytest, basedpyright, mypy           |
| `just q-lint`          | ruff with unsafe fixes, by hand (review `git diff`)         |
| `just q-fast`          | prek hooks only                                             |
| `just q-test`          | pytest                                                      |
| `just rel-build`       | clean `dist` (except `.gitignore`) and `uv build`           |
| `just rel-publish yes` | `uv publish`; without `yes` it only prints what it would do |

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

## Bump, Build and Publish

Update the version in pyproject.toml,
update `uv.lock`,
clean `dist` (except `.gitignore`),
build the package
and publish to PyPI.

```shell
cd $(git rev-parse --show-toplevel) &&\
uv version --bump patch &&\
uv sync --all-packages &&\
find dist -type f -not -name '.gitignore' -delete &&\
uv build &&\
uv publish &&\
echo https://pypi.org/project/uv-upx
```

Same with recipes: `uv version --bump patch && just dev-sync && just rel-build && just rel-publish yes`.
Publish only with the maintainer's OK.
