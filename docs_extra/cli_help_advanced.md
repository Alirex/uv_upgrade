# CLI

**Usage**:

```console
$ [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `upgrade`
* `helpers`

## `upgrade`

**Usage**:

```console
$ upgrade [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `run`: Update pyproject.toml dependencies to...

### `upgrade run`

Update pyproject.toml dependencies to latest compatible versions.

**Usage**:

```console
$ upgrade run [OPTIONS]
```

**Options**:

* `-p, --project PATH`: Path to project root directory. Use current working directory if not specified.
* `--dry-run`: Show changes without writing file
* `--verbose`: Show more output
* `--preserve-original-package-names`: Preserve original package names in pyproject.toml
* `--no-sync`: Do not run uv-sync. In case of the complex build process. But, recommended to run with sync, for better chances for revealing problems.
* `--version`: Show version and exit.
* `--help`: Show this message and exit.

## `helpers`

**Usage**:

```console
$ helpers [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `collect-top-level-dependencies-from-project`: Collect top-level dependencies from the...

### `helpers collect-top-level-dependencies-from-project`

Collect top-level dependencies from the project.

**Usage**:

```console
$ helpers collect-top-level-dependencies-from-project [OPTIONS]
```

**Options**:

* `-p, --project PATH`: Path to project root directory. Use current working directory if not specified.
* `--only-special-cases`: Collect only complex and unhandled dependencies
* `--preserve-original-package-names`: Preserve original package names in pyproject.toml
* `--help`: Show this message and exit.
