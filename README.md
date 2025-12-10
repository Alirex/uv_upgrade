# Uv upgrade

Upgrade dependencies in `pyproject.toml` files with `uv`.

---

# Install

For end-users.

Note: For developers, see the [dev](docs_extra/dev.md) section.

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

Or run with uvx:

```shell
uvx uv-upgrade
```

Dev installation: [see here](docs_extra/dev.md#install-app-system-wide-in-development-mode)

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

### Uv as a source of truth

Run `uv sync --all-groups --all-extras --all-packages --upgrade`.

Get dependencies versions from `uv.lock`.

Put them in `pyproject.toml` files.

### Workspace support

It works with workspaces. At least for some basic cases.

### Dependencies constraints

Now it handles only relatively simple cases.

So, it updates only `>=` dependencies.

This includes:

- single versions (`>=1.0.0`)
- ranges (`>=1.0.0, <2.0.0`)
  - Move lower bound to the new version.

Some dependencies constraints are skipped. Because i don't meet them yet.

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

If something goes wrong, it rolls back the changes to the `pyproject.toml` and `uv.lock` files.

### Why?

I needed this for my own projects.

I know these issues:

- [Upgrade dependencies in pyproject.toml (uv upgrade)](https://github.com/astral-sh/uv/issues/6692)
- [What is the intended workflow for updating dependencies with uv?](ttps://github.com/astral-sh/uv/issues/6794)

But I didn't see enough progress.

So, I implemented this tool for my own usage.

Maybe it will be useful for someone else.

### Why not in Rust?

Because it's a temporary Proof-of-Concept.

Maybe it will be replaced by Rust in the future.

It uses type annotations anyway. For simpler migration.

---

# Dev

[Dev](docs_extra/dev.md)

---

# Other similar tools comparison

[Other similar tools comparison](docs_extra/other_similar_tools_comparison.md)
