# Changelog

All notable changes to `uv-upx` are listed here. Format: [Keep a Changelog](https://keepachangelog.com/),
versions: [SemVer](https://semver.org/) (breaking or new feature = minor while `0.x`).

## [Unreleased]

### Changed

- Git history rewritten on 2026-11-28 to replace a personal commit e-mail: every commit SHA changed, and the tags
  (`v0.5.0` and the `archive/` tags) keep their names but point at the rewritten commits. Released packages on PyPI
  are unchanged. A clone from before that date needs `git fetch --force --tags` and a reset of `main`.
- Dependencies upgraded (`uv lock --upgrade`); nothing in the CLI changed.
- README: a before/after example on the first screen, badges, one H1; the behaviour notes moved to
  `docs_extra/behaviour.md`. The PyPI page links to the files of its release tag, not `main`.

### Fixed

- A constraint equal to the locked version by its numbers (`>=1.0` with `1.0.0` locked) is no longer rewritten.

## [0.5.0] - 2026-10-25

### Added

- `--keep-unconstrained`: a dependency written without a version constraint is left alone (by default it gets
  `>=<locked version>`).
- `--version` for `uv-upx`; `uvx` usage of the short command is documented.

### Changed

- Workspace members are skipped when upgrading dependencies.

### Fixed

- The fallback for versions with a local segment (`1.2.3+cpu`).

## [0.4.3] and earlier

See the git history.

[Unreleased]: https://github.com/Alirex/uv_upgrade/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/Alirex/uv_upgrade/releases/tag/v0.5.0
