# Brand book: uv-upx

Name: `uv-upx`. Tagline: "Constraints that follow the lock." The name, colours, fonts and marks are one source,
[brand/brand.yaml](../brand/brand.yaml), with the master SVGs in [brand/masters/](../brand/masters/); this page is the
prose around them. The package name is kept as published on PyPI (see the decision record in docs/decisions/).

## Mission

Raise the dependency constraints in pyproject.toml to the versions uv locks, and keep the file as written.

## Vision

Upgrading a uv project's floors is one command, with nothing to undo by hand when it fails.

## Audience

Python developers who manage projects or workspaces with uv and want the `>=` floors in `pyproject.toml` to match what they actually test against. Second: AI agents that run the upgrade as one step of a maintenance task.

## Values

1. **uv decides versions.** uv-upx only rewrites constraints; resolving and locking stay with `uv lock`.
2. **Keep what the author wrote.** Comments, layout and upper bounds in `pyproject.toml` survive the rewrite.
3. **Undo on failure.** A failed lock or sync rolls back `pyproject.toml` and `uv.lock`.

## Voice

Plain and exact: say what the tool does to which file, with the command that shows it. No marketing words.

| Do                                                  | Do not                                                 |
| --------------------------------------------------- | ------------------------------------------------------ |
| Write "`>=2.10.0` becomes `>=2.12.5`; `<3` is kept" | Write "keeps your dependencies fresh automatically"    |
| Keep the name in code type: `uv-upx`                | Capitalise it, translate it or add a logo-style suffix |

## Logo rules

The mark is an upward arrow over a base line in the ink colour, with one dot in the accent colour. Use it as supplied, on the paper
colour or a calm background; keep a quarter of its width free on every side; 16 px is the smallest size (use the small
mark there). Do not stretch, rotate, recolour or add effects. The artwork is CC-BY-4.0; a fork uses its own name and
mark.
