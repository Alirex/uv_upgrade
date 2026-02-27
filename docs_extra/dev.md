# Dev

## Rust install or update

https://www.rust-lang.org/tools/install

```bash
if ! command -v rustc &> /dev/null; then
    curl --proto '=https' --tlsv1.2 -LsSf https://sh.rustup.rs | sh
else
    rustup update
fi

rustc --version
```


## Install prek for pre-commit hooks

https://github.com/j178/prek?tab=readme-ov-file#installation

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

## Create venv

```bash
uv sync --all-packages
```

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
prek run --all-files
```

Useful after changing the hooks. Or just to check if everything is fine.

## Update dependencies

### Check available tools

```shell
cargo install --list
```

### Install cargo-update

Updater for system-wide cargo packages.

```shell
if ! command -v cargo-install-update &> /dev/null; then
    cargo install cargo-update
else
  cargo install-update cargo-update
fi

cargo-install-update --version
```

### Install cargo-edit

```bash
if ! command -v cargo-upgrade &> /dev/null; then
    cargo install cargo-edit
else
  cargo install-update cargo-edit
fi

cargo-upgrade --version
```

### Upgrade dependencies

```shell
cargo upgrade
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
find dist -type f -not -name '.gitignore' -delete ;\
uv build --all-packages &&\
uv publish --username __token__ --password ${PYPI_TOKEN} &&\
echo https://pypi.org/project/uv-upx
```
