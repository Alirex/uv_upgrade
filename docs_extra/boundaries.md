# Boundaries: what uv-upx owns and what uv owns

uv-upx is one deployable CLI (a modular monolith); nothing is split
([HQ service-boundaries](https://github.com/evocaslab/hq/blob/main/practices/service-boundaries.md)).

| Concern                                                                    | Owner                | Where in the code                                                   |
| -------------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------- |
| Resolving versions, the lock file, the environment                         | uv                   | `uv lock --upgrade`, `uv sync` (`services/run_uv_related/`)         |
| The meaning of `uv.lock`                                                   | uv (format)          | read only, by `services/dependencies_from_project/` into a registry |
| Which constraints to raise, which to keep (profiles, pinned, upper bounds) | uv-upx               | `services/dependency_up/`                                           |
| Reading and rewriting `pyproject.toml` (comments and layout kept)          | uv-upx, with tomlkit | `services/toml/`, `services/collect_dependencies/`                  |
| Rollback when uv or the rewrite fails                                      | uv-upx               | `services/updater/rollback_updater.py`                              |

Rules: uv is called only as a subprocess through `run_uv_related/` (tests use `tests/fake_uv.py`); the lock file is
read, never written by uv-upx; the registry (`DependenciesRegistry`) is the one way lock data reaches the rewrite.
