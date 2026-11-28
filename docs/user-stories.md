# User stories: uv-upx

Reviewed against the code on 2026-11-28.

One entry per goal a person or agent reaches with uv-upx, the Given/When/Then lines that confirm it, and the
test that proves it. Status: `built` (every line names a test that exists), `partial`, `planned`, `gap`.

## Index

| Id   | Goal                                                        | Actor                     | Status |
| ---- | ----------------------------------------------------------- | ------------------------- | ------ |
| US-1 | raise the constraints of a workspace to the locked versions | Python developer using uv | built  |
| US-2 | see the changes without keeping them                        | Python developer using uv | built  |
| US-3 | recover from a failed uv step                               | Python developer using uv | built  |
| US-4 | run the upgrade from an agent and read a machine result     | AI agent                  | gap    |

## US-1: raise the constraints of a workspace to the locked versions

```yaml
schema: 1
id: US-1
actor: Python developer using uv
goal: raise the constraints of a workspace to the locked versions
why: so that the floors match the versions the project is tested with
status: built
accept:
  - gwt: Given a workspace with old floors, when the upgrade runs, then every pyproject.toml gets the locked versions.
    test: test_upgrade_workspace
  - gwt: Given a project, when the upgrade runs, then pyproject.toml is written and uv sync runs.
    test: test_upgrade_writes_pyproject_and_syncs
proof:
  cmd: uv run pytest
```

## US-2: see the changes without keeping them

```yaml
schema: 1
id: US-2
actor: Python developer using uv
goal: see the changes without keeping them
why: so that the change can be reviewed before it is made
status: built
accept:
  - gwt: Given `--dry-run`, when the upgrade runs, then the files are restored afterwards.
    test: test_dry_run_restores_files
proof:
  cmd: uv run pytest
```

## US-3: recover from a failed uv step

```yaml
schema: 1
id: US-3
actor: Python developer using uv
goal: recover from a failed uv step
why: so that a failed upgrade leaves the project as it was
status: built
accept:
  - gwt: Given uv sync fails, when the upgrade runs, then pyproject.toml and uv.lock are rolled back.
    test: test_failed_sync_rolls_back
  - gwt: Given uv lock fails, when the upgrade runs, then the files are rolled back.
    test: test_failed_lock_rolls_back
proof:
  cmd: uv run pytest
```

## US-4: run the upgrade from an agent and read a machine result

```yaml
schema: 1
id: US-4
actor: AI agent
goal: run the upgrade from an agent and read a machine result
why: so that an agent can check what changed without parsing human text
status: gap
accept:
  - gwt: Given `--json`, when the upgrade runs, then it prints one JSON result with a schema_version.
    test: none yet
proof:
  cmd: none yet
```

## Retired

None.
