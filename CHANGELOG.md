# Changelog

All notable changes to `uv-upx` are listed here. Format: [Keep a Changelog](https://keepachangelog.com/),
versions: [SemVer](https://semver.org/) (breaking or new feature = minor while `0.x`).

## [Unreleased]

### Changed

- Dependencies upgraded (`uv lock --upgrade`); nothing in the CLI changed.

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
