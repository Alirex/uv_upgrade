//! A fake `uv` for the tests of `uv-upx` (the counterpart of `src/uv_upx/tests/fake_uv.py`): records every call,
//! plays `uv lock --upgrade` by copying a prepared lock file into place, and fails on request. Settings come from
//! the environment:
//!
//! - `FAKE_UV_LOG`: the file the calls are appended to, one line each (`uv lock --upgrade`).
//! - `FAKE_UV_LOCK_AFTER`: the file `uv lock --upgrade` copies to `uv.lock` in the current directory.
//! - `FAKE_UV_LOCK_RC`, `FAKE_UV_LOCK_STDERR`: `uv lock` exits with this code (when not 0) after printing the text.
//! - `FAKE_UV_LOCK_FAIL_ONCE`: `1` makes only the first `uv lock` fail (the local-segment fallback retries).
//! - `FAKE_UV_SYNC_FAILS`: `1` makes `uv sync` fail, except the `--frozen` one of the rollback.

use std::ffi::OsString;
use std::io::Write;
use std::path::PathBuf;
use std::process::ExitCode;

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    match run(&args) {
        Ok(code) => code,
        Err(message) => {
            eprintln!("fake uv: {message}");
            ExitCode::from(70)
        }
    }
}

fn setting(name: &str) -> Option<OsString> {
    std::env::var_os(name).filter(|value| !value.is_empty())
}

fn flag(name: &str) -> bool {
    setting(name).is_some_and(|value| value == "1")
}

fn path_setting(name: &str) -> Result<PathBuf, String> {
    setting(name)
        .map(PathBuf::from)
        .ok_or_else(|| format!("{name} is not set"))
}

fn run(args: &[String]) -> Result<ExitCode, String> {
    let log = path_setting("FAKE_UV_LOG")?;
    let mut log_file = std::fs::OpenOptions::new()
        .append(true)
        .create(true)
        .open(&log)
        .map_err(|error| format!("cannot open {}: {error}", log.display()))?;
    writeln!(log_file, "uv {}", args.join(" ")).map_err(|error| error.to_string())?;

    match args.first().map(String::as_str) {
        Some("lock") => lock(args, &log),
        Some("sync") => Ok(sync(args)),
        _ => Ok(ExitCode::SUCCESS),
    }
}

fn lock(args: &[String], log: &PathBuf) -> Result<ExitCode, String> {
    if args.iter().any(|arg| arg == "--upgrade") {
        let lock_after = path_setting("FAKE_UV_LOCK_AFTER")?;
        std::fs::copy(&lock_after, "uv.lock")
            .map_err(|error| format!("cannot copy {} to uv.lock: {error}", lock_after.display()))?;
    }
    let returncode: u8 = setting("FAKE_UV_LOCK_RC")
        .map_or_else(|| "0".to_owned(), |value| value.to_string_lossy().into_owned())
        .parse()
        .map_err(|error| format!("FAKE_UV_LOCK_RC: {error}"))?;
    let lock_calls = std::fs::read_to_string(log)
        .map_err(|error| error.to_string())?
        .lines()
        .filter(|line| line.starts_with("uv lock"))
        .count();
    let fails = returncode != 0 && !(flag("FAKE_UV_LOCK_FAIL_ONCE") && lock_calls > 1);
    if !fails {
        return Ok(ExitCode::SUCCESS);
    }
    if let Some(text) = setting("FAKE_UV_LOCK_STDERR") {
        // Best effort, like uv's own output: a closed stderr does not change the exit code.
        let _ = std::io::stderr().write_all(text.to_string_lossy().as_bytes());
    }
    Ok(ExitCode::from(returncode))
}

fn sync(args: &[String]) -> ExitCode {
    if flag("FAKE_UV_SYNC_FAILS") && !args.iter().any(|arg| arg == "--frozen") {
        return ExitCode::FAILURE;
    }
    ExitCode::SUCCESS
}
