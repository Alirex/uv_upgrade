//! Run `uv lock` and `uv sync` as subprocesses (`uv` from `PATH`, in the project directory).

use std::io::Write;
use std::path::Path;
use std::process::{Command, Stdio};

use crate::error::{Error, Result};

/// The text uv prints when a `>=` constraint meets a version with a local segment.
pub const ERROR_TEXT_PART_NON_EMPTY_LOCAL_SEGMENT: &str =
    "Operator >= is incompatible with versions containing non-empty local segments";

/// The arguments of `uv lock`.
#[must_use]
pub fn lock_args(upgrade: bool) -> Vec<&'static str> {
    let mut args = vec!["lock"];
    if upgrade {
        args.push("--upgrade");
    }
    args
}

/// The error of a failed `uv lock`, from what it printed.
#[must_use]
pub fn classify_lock_failure(stderr: &str) -> Error {
    if stderr.contains(ERROR_TEXT_PART_NON_EMPTY_LOCAL_SEGMENT) {
        Error::NonEmptyLocalSegments
    } else {
        Error::UnresolvedLock
    }
}

/// `uv lock`, with `--upgrade` when asked. uv's stderr is shown to the user after the run (it is captured to detect
/// the local-segment error); its stdout passes through.
///
/// # Errors
///
/// `Error::NonEmptyLocalSegments` or `Error::UnresolvedLock` on a non-zero exit, `Error::UvNotRunnable` when `uv`
/// cannot be started.
pub fn run_uv_lock(workdir: &Path, upgrade: bool) -> Result<()> {
    let output = Command::new("uv")
        .args(lock_args(upgrade))
        .current_dir(workdir)
        .stdin(Stdio::inherit())
        .stdout(Stdio::inherit())
        .stderr(Stdio::piped())
        .output()
        .map_err(Error::UvNotRunnable)?;

    // Best effort, like `sys.stderr.write`: a closed stderr is not an error of the upgrade.
    let _ = std::io::stderr().write_all(&output.stderr);

    if output.status.success() {
        return Ok(());
    }
    Err(classify_lock_failure(&String::from_utf8_lossy(&output.stderr)))
}

/// How `uv sync` runs.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum UvSyncMode {
    /// `--upgrade`
    Upgrade,
    /// `--frozen`: install exactly the lock file (the rollback).
    Frozen,
    /// No extra flag.
    Default,
}

/// The arguments of `uv sync`: `--all-groups --all-extras --all-packages` when `include_all`, then the mode's flag.
#[must_use]
pub fn sync_args(uv_sync_mode: UvSyncMode, include_all: bool) -> Vec<&'static str> {
    let mut args = vec!["sync"];
    if include_all {
        args.extend(["--all-groups", "--all-extras", "--all-packages"]);
    }
    match uv_sync_mode {
        UvSyncMode::Upgrade => args.push("--upgrade"),
        UvSyncMode::Frozen => args.push("--frozen"),
        UvSyncMode::Default => {}
    }
    args
}

/// `uv sync` (see [`sync_args`]).
///
/// # Errors
///
/// `Error::UnresolvedSync` on a non-zero exit, `Error::UvNotRunnable` when `uv` cannot be started.
pub fn run_uv_sync(workdir: &Path, uv_sync_mode: UvSyncMode, include_all: bool) -> Result<()> {
    let status = Command::new("uv")
        .args(sync_args(uv_sync_mode, include_all))
        .current_dir(workdir)
        .status()
        .map_err(Error::UvNotRunnable)?;
    if status.success() {
        Ok(())
    } else {
        Err(Error::UnresolvedSync)
    }
}

#[cfg(test)]
mod tests {
    use super::{ERROR_TEXT_PART_NON_EMPTY_LOCAL_SEGMENT, UvSyncMode, classify_lock_failure, lock_args, sync_args};
    use crate::error::Error;

    #[test]
    fn lock_args_cases() {
        assert_eq!(lock_args(false), vec!["lock"]);
        assert_eq!(lock_args(true), vec!["lock", "--upgrade"]);
    }

    #[test]
    fn lock_failure_classification() {
        assert!(matches!(
            classify_lock_failure(&format!("error: {ERROR_TEXT_PART_NON_EMPTY_LOCAL_SEGMENT}\n")),
            Error::NonEmptyLocalSegments
        ));
        assert!(matches!(
            classify_lock_failure("error: No solution found\n"),
            Error::UnresolvedLock
        ));
    }

    #[test]
    fn sync_args_cases() {
        assert_eq!(
            sync_args(UvSyncMode::Default, true),
            vec!["sync", "--all-groups", "--all-extras", "--all-packages"]
        );
        assert_eq!(
            sync_args(UvSyncMode::Frozen, true),
            vec!["sync", "--all-groups", "--all-extras", "--all-packages", "--frozen"]
        );
        assert_eq!(sync_args(UvSyncMode::Upgrade, false), vec!["sync", "--upgrade"]);
    }
}
