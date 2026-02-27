# Command-Line Help for `uv-upx`

This document contains the help content for the `uv-upx` command-line program.

**Command Overview:**

* [`uv-upx`↴](#uv-upx)
* [`uv-upx upgrade`↴](#uv-upx-upgrade)
* [`uv-upx cli-helpers`↴](#uv-upx-cli-helpers)
* [`uv-upx cli-helpers export-cli-help`↴](#uv-upx-cli-helpers-export-cli-help)
* [`uv-upx cli-helpers generate-shell-completion`↴](#uv-upx-cli-helpers-generate-shell-completion)

## `uv-upx`

Update pyproject.toml dependencies to latest compatible versions.

**Usage:** `uv-upx <COMMAND>`

###### **Subcommands:**

* `upgrade` — 1 Update pyproject.toml dependencies to latest compatible versions
* `cli-helpers` — CLI Helpers



## `uv-upx upgrade`

1 Update pyproject.toml dependencies to latest compatible versions

**Usage:** `uv-upx upgrade [OPTIONS]`

###### **Options:**

* `-p`, `--project <PATH>` — Path to the project root directory. Use the current working directory if not specified
* `--verbose` — Show more output
* `--preserve-original-package-names` — Preserve original package names in pyproject.toml
* `--no-sync` — Do not run uv-sync
* `--profile <PROFILE>` — Which profile to use when upgrading dependencies. (Experimental feature)

  Possible values:
  - `default`:
    Default profile
  - `with-pinned`:
    Upgrade also "pinned" (== exact version) dependencies

* `--interactive` — Enable interactive mode for selecting updates. (Experimental feature)



## `uv-upx cli-helpers`

CLI Helpers

**Usage:** `uv-upx cli-helpers <COMMAND>`

###### **Subcommands:**

* `export-cli-help` — Export cli help as Markdown
* `generate-shell-completion` — Generate shell completion



## `uv-upx cli-helpers export-cli-help`

Export cli help as Markdown

**Usage:** `uv-upx cli-helpers export-cli-help --output <PATH>`

###### **Options:**

* `--output <PATH>` — Path to the output file



## `uv-upx cli-helpers generate-shell-completion`

Generate shell completion

**Usage:** `uv-upx cli-helpers generate-shell-completion <SHELL>`

###### **Arguments:**

* `<SHELL>`

  Possible values: `bash`, `elvish`, `fish`, `nushell`, `powershell`, `zsh`




