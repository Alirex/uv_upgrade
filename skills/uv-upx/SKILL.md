---
name: uv-upx
description: Upgrade the dependency constraints in pyproject.toml of a uv project or workspace with uv-upx. Use when the user asks to bump or raise Python dependency floors to the locked versions in a uv-managed project.
---

# uv-upx

Run it in the project or workspace root (the folder with the top `pyproject.toml`):

| Goal                                                | Command                                    |
| --------------------------------------------------- | ------------------------------------------ |
| Raise `>=` floors to the locked versions, then sync | `uv-upgrade`                               |
| Same, without `uv sync` (relock only)               | `uv-upx upgrade run --no-sync`             |
| Show the changes, keep nothing                      | `uv-upx upgrade run --dry-run`             |
| Leave dependencies without a constraint alone       | `uv-upx upgrade run --keep-unconstrained`  |
| Also move `==` pins                                 | `uv-upx upgrade run --profile with_pinned` |

Install it with `uv tool install uv-upx`. Check the result with `git diff` on the `pyproject.toml` files: only
constraints change, comments and layout stay. Upper bounds (`<`, `<=`, `~=`) are kept on purpose. A failed run
restores `pyproject.toml` and `uv.lock`. There is no `--json` output yet: read the exit code and the diff.

## Rules

- This skill runs no scripts and fetches nothing; it tells you which command or API to use.
- Read the README before you change how the project is used; the repo's own rules for agents are in AGENTS.md.
