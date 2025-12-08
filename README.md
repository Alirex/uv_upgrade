# Uv upgrade

Upgrade dependencies in `pyproject.toml` with `uv`.

---

# Install

For end-users.

Note: For developers, see the [Dev](#dev) section.

## Uv install or update

You need this for both usage and development.

https://docs.astral.sh/uv/getting-started/installation/

On Windows it can be better to use `Git Bash` terminal.

```bash
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh;
else
    uv self update;
fi

uv --version
```

## Install or update a project for system-wide usage

Run it from any directory, except the project directory.

```shell
if ! command -v uv-upgrade &> /dev/null; then
    uv tool install git+https://github.com/Alirex/uv_upgrade
else
    uv tool upgrade uv-upgrade
fi
```

Dev installation: [see here](#install-app-system-wide-in-development-mode)

## Check that project in the list

```shell
uv tool list --show-python
```

## Remove the project with all data

If you need to remove the project with all data, run this command from the project directory:

```shell
uv tool uninstall uv-upgrade
```

---

# Usage

## Run the tool in the folder with the pyproject.toml

After installation, you can run the tool from any directory.

```shell
uv-upgrade
```

Also, you can run it with the `--help` flag with more details.

## Notes

### Dependencies constraints

Now it handles only relatively simple cases.

So, it updates only `>=` dependencies.

Other dependencies constraints are skipped. Like:

- ranges (`>=1.0.0, <2.0.0`)

Some are skipped by design (for now). Like:

- `==` constraints

But it can be changed with "options" in the future.

### Style preservation

It preserves comments in the `pyproject.toml` file. Like here:

```toml
dependencies = [
    # Better classes and data validation
    "pydantic>=2.12.5",
    # TOML parser and writer with preserved formatting
    "tomlkit>=0.13.3",
    # CLI app framework
    "typer>=0.20.0",
]
```

### Rollback

It changes the `pyproject.toml`.

Then run `uv lock` to update the lock file.

During the update, `uv` resolves the dependencies.

If something goes wrong, it rolls back the changes to the `pyproject.toml`.

### Why?

I needed this for my own projects.

I know these issues:

- [Upgrade dependencies in pyproject.toml (uv upgrade)](https://github.com/astral-sh/uv/issues/6692)
- [What is the intended workflow for updating dependencies with uv?](ttps://github.com/astral-sh/uv/issues/6794)

But I didn't see enough progress.

So, I implemented this tool for my own usage.

Maybe it will be useful for someone else.

### Why not in PyPI?

This is a temporary solution.
It must be replaced by `uv upgrade` command from `uv` in the future.

### Why not in Rust?

Because it's a temporary Proof-of-Concept.

Maybe it will be replaced by Rust in the future.

It uses type annotations anyway. For simpler migration.

---

# Dev

## Uv install or update

https://docs.astral.sh/uv/getting-started/installation/

```bash
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh;
else
    uv self update;
fi

uv --version
```

## Ruff install or update

https://docs.astral.sh/ruff/installation/

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

## Install app system-wide in Development mode

For system-wide usage during development, run this command from the repository directory:

```shell
uv tool install --editable .
```
