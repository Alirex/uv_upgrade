//! Shared helpers of the integration tests: a fake `uv` on `PATH` and fixture projects.
//!
//! The fake `uv` is a shell script (Unix only): it records every call, plays `uv lock --upgrade` by copying a
//! prepared lock file into place, and fails on request, like `fake_uv.py` of the Python tests.

#![expect(dead_code, reason = "each test binary uses a different subset of the helpers")]
#![expect(clippy::unwrap_used, reason = "a test panics on an unexpected value")]

use std::path::{Path, PathBuf};
use std::process::{Command, Output};

use tempfile::TempDir;

/// The fake `uv` of one test.
pub struct FakeUv {
    dir: TempDir,
    lock_returncode: i32,
    lock_stderr: String,
    lock_fail_once: bool,
    sync_fails: bool,
}

const SCRIPT: &str = r#"#!/usr/bin/env bash
set -eu
printf 'uv %s\n' "$*" >> "$FAKE_UV_LOG"
case "${1:-}" in
  lock)
    for arg in "$@"; do
      if [ "$arg" = "--upgrade" ]; then cp "$FAKE_UV_LOCK_AFTER" uv.lock; fi
    done
    fail=1
    if [ "${FAKE_UV_LOCK_FAIL_ONCE:-0}" = 1 ] && [ "$(grep -c '^uv lock' "$FAKE_UV_LOG")" -gt 1 ]; then fail=0; fi
    if [ "$fail" = 1 ] && [ "${FAKE_UV_LOCK_RC:-0}" != 0 ]; then
      if [ -n "${FAKE_UV_LOCK_STDERR:-}" ]; then printf '%s' "$FAKE_UV_LOCK_STDERR" >&2; fi
      exit "${FAKE_UV_LOCK_RC}"
    fi
    ;;
  sync)
    if [ "${FAKE_UV_SYNC_FAILS:-0}" = 1 ]; then
      case " $* " in *" --frozen "*) exit 0 ;; *) exit 1 ;; esac
    fi
    ;;
esac
"#;

impl FakeUv {
    /// A fake `uv` whose `uv lock --upgrade` writes `lock_after_upgrade` to `uv.lock`.
    pub fn new(lock_after_upgrade: &str) -> Self {
        let dir = tempfile::tempdir().unwrap();
        let bin = dir.path().join("bin");
        std::fs::create_dir(&bin).unwrap();
        let script = bin.join("uv");
        std::fs::write(&script, SCRIPT).unwrap();
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            std::fs::set_permissions(&script, std::fs::Permissions::from_mode(0o755)).unwrap();
        }
        std::fs::write(dir.path().join("lock_after"), lock_after_upgrade).unwrap();
        std::fs::write(dir.path().join("log"), "").unwrap();
        Self {
            dir,
            lock_returncode: 0,
            lock_stderr: String::new(),
            lock_fail_once: false,
            sync_fails: false,
        }
    }

    /// `uv lock` fails with this exit code and stderr.
    #[must_use]
    pub fn lock_fails(mut self, returncode: i32, stderr: &str) -> Self {
        self.lock_returncode = returncode;
        stderr.clone_into(&mut self.lock_stderr);
        self
    }

    /// Only the first `uv lock` fails (the local-segment fallback retries).
    #[must_use]
    pub fn lock_fails_once(mut self, stderr: &str) -> Self {
        self.lock_fail_once = true;
        self.lock_fails(1, stderr)
    }

    /// `uv sync` fails, except the `--frozen` one of the rollback.
    #[must_use]
    pub fn sync_fails(mut self) -> Self {
        self.sync_fails = true;
        self
    }

    /// Put the fake `uv` first on `PATH` of a command and pass it its settings.
    pub fn apply<'c>(&self, command: &'c mut Command) -> &'c mut Command {
        let bin = self.dir.path().join("bin");
        let path = std::env::var_os("PATH").unwrap_or_default();
        let mut paths = vec![bin];
        paths.extend(std::env::split_paths(&path));
        command
            .env("PATH", std::env::join_paths(paths).unwrap())
            .env("FAKE_UV_LOG", self.dir.path().join("log"))
            .env("FAKE_UV_LOCK_AFTER", self.dir.path().join("lock_after"))
            .env("FAKE_UV_LOCK_RC", self.lock_returncode.to_string())
            .env("FAKE_UV_LOCK_STDERR", &self.lock_stderr)
            .env("FAKE_UV_LOCK_FAIL_ONCE", if self.lock_fail_once { "1" } else { "0" })
            .env("FAKE_UV_SYNC_FAILS", if self.sync_fails { "1" } else { "0" })
    }

    /// The recorded calls, like `uv lock --upgrade`.
    pub fn commands(&self) -> Vec<String> {
        std::fs::read_to_string(self.dir.path().join("log"))
            .unwrap()
            .lines()
            .map(ToOwned::to_owned)
            .collect()
    }

    /// Forget the recorded calls.
    pub fn reset(&self) {
        std::fs::write(self.dir.path().join("log"), "").unwrap();
    }
}

/// The recorded `uv lock --upgrade`.
pub const UPGRADE: &str = "uv lock --upgrade";
/// The recorded `uv sync` of the finalization.
pub const SYNC: &str = "uv sync --all-groups --all-extras --all-packages";
/// The recorded `uv sync --frozen` of the rollback.
pub const SYNC_FROZEN: &str = "uv sync --all-groups --all-extras --all-packages --frozen";

/// The single-project fixture of the Python updater tests.
pub const PYPROJECT: &str =
    "[project]\nname = \"demo\"\nversion = \"0.1.0\"\ndependencies = [\n    # HTTP client\n    \"httpx>=0.24.0\",\n]\n";
/// Its lock before the upgrade.
pub const LOCK_BEFORE: &str = "version = 1\n\n[[package]]\nname = \"httpx\"\nversion = \"0.24.0\"\n";

/// Its lock after the upgrade.
pub fn lock_after() -> String {
    LOCK_BEFORE.replace("\"0.24.0\"", "\"0.28.1\"")
}

/// The workspace fixture of the Python `test_updater.py`.
pub const ROOT_PYPROJECT: &str = r#"[project]
name = "root"
version = "0.1.0"
dependencies = [
    # HTTP client
    "httpx>=0.24.0",
    "context",
]

[project.optional-dependencies]
cli = ["rich"]

[dependency-groups]
dev = [
    "pytest>=8.0",
    { include-group = "lint" },
]
lint = []

[tool.uv.sources]
context = { workspace = true }

[tool.uv.workspace]
members = ["packages/*"]
"#;

/// Its member.
pub const MEMBER_PYPROJECT: &str = "[project]\nname = \"context\"\nversion = \"0.1.0\"\ndependencies = [\n    \"pydantic==2.0.0\",\n    \"httpx\",\n]\n";

/// The workspace lock (the versions after `uv lock --upgrade`).
pub const WORKSPACE_LOCK: &str = r#"
[[package]]
name = "httpx"
version = "0.28.1"

[[package]]
name = "pydantic"
version = "2.12.5"

[[package]]
name = "pytest"
version = "9.0.1"

[[package]]
name = "rich"
version = "14.2.0"
"#;

/// Write a file, creating the directories.
pub fn write(path: &Path, text: &str) {
    std::fs::create_dir_all(path.parent().unwrap()).unwrap();
    std::fs::write(path, text).unwrap();
}

/// Read a file.
pub fn read(path: &Path) -> String {
    std::fs::read_to_string(path).unwrap()
}

/// A single project in a temp dir: `pyproject.toml` and `uv.lock`.
pub fn project(pyproject: &str, lock: &str) -> TempDir {
    let dir = tempfile::tempdir().unwrap();
    write(&dir.path().join("pyproject.toml"), pyproject);
    write(&dir.path().join("uv.lock"), lock);
    dir
}

/// The workspace fixture in a temp dir; returns it and the member directory.
pub fn workspace() -> (TempDir, PathBuf) {
    let dir = project(ROOT_PYPROJECT, "version = 1\n");
    let member = dir.path().join("packages").join("context");
    write(&member.join("pyproject.toml"), MEMBER_PYPROJECT);
    (dir, member)
}

/// The `uv-upx` binary under test.
pub fn uv_upx() -> Command {
    Command::new(env!("CARGO_BIN_EXE_uv-upx"))
}

/// The `uv-upgrade` binary under test.
pub fn uv_upgrade() -> Command {
    Command::new(env!("CARGO_BIN_EXE_uv-upgrade"))
}

/// Run a command and return its output.
pub fn run(command: &mut Command) -> Output {
    command.output().unwrap()
}

/// The stdout of an output as text.
pub fn stdout(output: &Output) -> String {
    String::from_utf8_lossy(&output.stdout).into_owned()
}

/// The stderr of an output as text.
pub fn stderr(output: &Output) -> String {
    String::from_utf8_lossy(&output.stderr).into_owned()
}

/// The log lines of a stderr without their timestamps (`name - LEVEL - message`); other lines are dropped.
pub fn log_lines(text: &str) -> Vec<String> {
    text.lines()
        .filter_map(|line| {
            // "2026-10-25 12:34:56,789 - name - INFO - message"
            let (stamp, rest) = line.split_once(" - ")?;
            let looks_like_stamp = stamp.len() == 23
                && stamp.as_bytes().get(4) == Some(&b'-')
                && stamp.as_bytes().get(10) == Some(&b' ')
                && stamp.as_bytes().get(19) == Some(&b',');
            looks_like_stamp.then(|| rest.to_owned())
        })
        .collect()
}
