# handle_version_constraint: logging-only parameters and complexity

Smell scan 2026-11-10 (radon C 11; `verbose` and `dependency` exist only to log: a flag argument plus a data clump) at
`src/uv_upx/services/dependency_up/update_dependency.py:71`. The caller never passes them, so the log branches are dead
in production.

Done when: the dead branches are removed or wired to the caller. Characterization first: `test_version_constraints.py`
and `test_properties.py` already pin the behaviour.
