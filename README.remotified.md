# Uv upgrade

Upgrade dependencies in `pyproject.toml` files with `uv`.

---

# Install

For end-users.

Note: For developers, see the [dev](https://github.com/Alirex/uv_upgrade/blob/main/docs_extra/dev.md) section.

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

This will install or upgrade the tool.

```shell
if ! command -v uv-upx &> /dev/null; then
    uv tool install uv-upx
else
    uv tool upgrade uv-upx
fi

uv-upgrade --version
```

Or run advanced version with uvx:

```shell
uvx uv-upx
```

Dev installation: [see here](https://github.com/Alirex/uv_upgrade/blob/main/docs_extra/dev.md#install-app-system-wide-in-development-mode)

## Check that project in the list

```shell
uv tool list --show-python
```

## Remove the project with all data

If you need to remove the project with all data, run this command from the project directory:

```shell
uv tool uninstall uv-upx
```

---

# Usage

## Run the tool in the folder with the pyproject.toml

After installation, you can run the tool from any directory.

```shell
uv-upgrade
```

or

```shell
uv-upx upgrade run
```

It is the same. But `uv-upx` provides more features.

## Get help

You can run commands with the `--help` flag with more details.

Exported versions:

- for `uv-upgrade`:
  - [cli_help_simple.md](https://github.com/Alirex/uv_upgrade/blob/main/docs_extra/cli_help_simple.md)
- for `uv-upx`:
  - [cli_help_advanced.md](https://github.com/Alirex/uv_upgrade/blob/main/docs_extra/cli_help_advanced.md)

## Install CLI completion (Optional)

This will install completion for the current shell. Available after restarting the shell.

- for `uv-upgrade`:
  - ```shell
    uv-upgrade --install-completion
    ```

  ```

  ```

  ```

  ```

- for `uv-upx`:
  - ```shell
    uv-upx --install-completion
    ```

  ```

  ```

  ```

  ```

Note: relatively safe to run multiple times. It just adds extra newlines to your shell config when run multiple times.

## Notes

### Uv as a source of truth

Run `uv sync --all-groups --all-extras --all-packages --upgrade`.

Get dependencies versions from `uv.lock`.

Put them in `pyproject.toml` files in related groups.

So, the main responsibility for dependencies resolution is on `uv`.

### Workspace support

It works with workspaces. At least for some basic cases.

Respects:

- both `members` and `exclude` sections.
- glob-based patterns.

### Normalize dependencies names

For example:

- `TOMLKit` -> `tomlkit`
- `Pydantic` -> `pydantic`
- `pyTEST_BenchMark` -> `pytest-benchmark`

### Updates simple dependencies

Updates `>=` dependencies. Like `bla>=2.0.0`.

Because, in this case, we can simply put the new version instead of the old one.

Update the similar part of the constraint in the multi-constraint.

### Skip pinned versions and upper bounds

It doesn't touch pinned versions. Like `bla==2.0.0`.

It doesn't touch lower bounds. Like:

- `bla<=2.0.0`
- `bla~=2.0.0`

### Respect simple ranges and some combined constraints

It respects simple dependency ranges. Like `bla>=1.0.0,<2.0.0`.

It moves the lower bound to the new version.

In fact, it handles any part of the constraint with a supported operator.

### Respect extras

It respects extras. Like `bla[dev]>=1.0.0;python_version>="3.14"`.

### Fix undefined constraints with lower bound to the new version

It sets undefined lower bounds to the new version.

For example, before:

```toml
dependencies = [
    "foo>=1.0.0",
    "bla",
]
```

After:

```toml
dependencies = [
    "foo>=1.0.0",
    "bla>=2.0.0",
]
```

### Skip unhandled constraints

It skips unhandled and complex constraints. Like:

- `bla<1.0.0`

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

### Rollback on no-changes

If nothing from pyproject.toml was changed, it rolls back the changes to the `uv.lock` file.

So, only top-level dependencies changes trigger a `uv.lock` update.

### Upgrade `equal`/`pinned` dependencies

Honestly, I think it's insecure to upgrade pinned dependencies automatically.
Because they must be pinned for a reason.

For applications that require strict control of dependencies, maybe better to use `frozen` mode of `uv sync`.

But for someone it can be useful to upgrade pinned dependencies automatically.

And we can do it.

```shell
uv-upgrade --profile with_pinned
```

It handles only `equal` (`==`) and NOT `strictly equal` (`===`) operators.

So, even in this mode, it won't change `bla===2.0.0`.

Under the hood it:

- collect all top-level dependencies information
- changes `==` version constraints to `>=`
- runs the standard upgrade process by `uv`
- upgrade `pyproject.toml` files accordingly with returning `==` constraints back

Note: more `upgrade` profiles can be added later. Or/and custom verbose `features` options.

Note: Can be combined with `--interactive` mode.

### Interactive mode

You can run the tool in interactive mode.

You must `Accept` or `Reject` each proposed change.

```shell
uv-upgrade --interactive
```

Demo example:
![demo_interactive.png](https://raw.githubusercontent.com/Alirex/uv_upgrade/main/docs_extra/images/demo_interactive.png)

### Get special cases

This allows you to see all the top-level dependencies that have some special constraints.
Like:

- ranges (`bla>=1.0.0,<2.0.0`)
- not defined bounds (`bla`)
- equal/pinned dependencies (`bla==2.0.0`)
- unhandled constraints (`bla<1.0.0`)

```shell
uv-upx helpers collect-top-level-dependencies-from-project --only-special-cases
```

### Why?

I needed this for my own projects.

I know these issues:

- [Upgrade dependencies in pyproject.toml (uv upgrade)](https://github.com/astral-sh/uv/issues/6692)
- [What is the intended workflow for updating dependencies with uv?](https://github.com/astral-sh/uv/issues/6794)

But I didn't see enough progress.

So, I implemented this tool for my own usage.

Maybe it will be useful for someone else.

### Why not in Rust?

Because it's a temporary Proof-of-Concept.

Maybe it will be replaced by Rust in the future.

It uses type annotations anyway. For simpler migration.

---

# Dev

[Dev](https://github.com/Alirex/uv_upgrade/blob/main/docs_extra/dev.md)

---

# Other similar tools comparison

[Other similar tools comparison](https://github.com/Alirex/uv_upgrade/blob/main/docs_extra/other_similar_tools_comparison.md)
