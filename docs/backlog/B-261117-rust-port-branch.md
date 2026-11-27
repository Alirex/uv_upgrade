---
id: B-261117-rust-port-branch
status: design
requested: 2026-11-17
size: m
---

# Finish or drop the Rust port branch

Found in the loose-ends round of 2026-11-17. The branch `feat/rust-port-followups` (pushed, tip `d1b5731`, 3 weeks old,
4 commits, about 5,500 added lines) ports `uv-upx` to Rust in `rust/uv_upx`: parity tests, cargo hooks and recipes in
the gate, a CI rust job, a maturin bin wheel, `docs_extra/rust_rework.md` with the state, distribution plan and
switch-over checklist, and a Rust `fake_uv` test binary. `feat/rust-port` (tip `c53b7d2`) is its ancestor and was
removed locally; the remote branch is still there.

It is not merged: `main` has moved on (AGENTS.md, README, gate config), the gate has not run on the merged tree, and
AGENTS.md says a started Rust rewrite lives on `features/rust` and must not be merged unasked. Decide: continue the port
(merge `origin/main`, run `just q-check`, follow the switch-over checklist) or close it.

Done when: the branch is landed or deleted (with the maintainer's OK) and this file is deleted.
