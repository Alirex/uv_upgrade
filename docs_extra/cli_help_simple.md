# `run`

Update pyproject.toml dependencies to latest compatible versions.

**Usage**:

```console
$ run [OPTIONS]
```

**Options**:

* `-p, --project PATH`: Path to project root directory. Use current working directory if not specified.
* `--dry-run`: Show changes without writing file
* `--verbose`: Show more output
* `--preserve-original-package-names`: Preserve original package names in pyproject.toml
* `--no-sync`: Do not run uv-sync. In case of the complex build process. But, recommended to run with sync, for better chances for revealing problems.
* `--version`: Show version and exit.
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.
