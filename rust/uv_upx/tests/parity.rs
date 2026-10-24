//! Parity with the Python implementation: both CLIs run on identical fixture projects with the same fake `uv`, and
//! the resulting files, stdout, log lines, exit codes and `uv` calls must be the same.
//!
//! The Python CLI comes from the repo's venv (`.venv/bin/uv-upx`, created by `uv sync`). Without it the tests are
//! skipped with a note, so `cargo test` works in a plain Rust checkout; the repo's gate runs `uv sync` first.

#![cfg(unix)]
#![expect(clippy::unwrap_used, reason = "a test panics on an unexpected value")]

mod common;

use std::path::{Path, PathBuf};
use std::process::Command;

use common::{FakeUv, LOCK_BEFORE, PYPROJECT, WORKSPACE_LOCK, lock_after, log_lines, run, stdout, write};
use tempfile::TempDir;

/// Which binary of each implementation runs.
#[derive(Clone, Copy)]
enum Bin {
    Full,
    Short,
}

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

fn python_bin(bin: Bin) -> Option<PathBuf> {
    let name = match bin {
        Bin::Full => "uv-upx",
        Bin::Short => "uv-upgrade",
    };
    let path = repo_root().join(".venv").join("bin").join(name);
    path.exists().then_some(path)
}

fn rust_bin(bin: Bin) -> PathBuf {
    PathBuf::from(match bin {
        Bin::Full => env!("CARGO_BIN_EXE_uv-upx"),
        Bin::Short => env!("CARGO_BIN_EXE_uv-upgrade"),
    })
}

/// One run of an implementation: everything the comparison looks at.
#[derive(Debug, PartialEq, Eq)]
struct Outcome {
    exit_code: Option<i32>,
    stdout: String,
    logs: Vec<String>,
    /// `None` when the file is gone (the pinned profile deletes `uv.lock`; the fake `uv lock` does not write it).
    files: Vec<(String, Option<String>)>,
    uv_calls: Vec<String>,
}

/// A fixture: the files of a project, relative to its root.
type Fixture = Vec<(&'static str, String)>;

fn simple_fixture(pyproject: &str) -> Fixture {
    vec![
        ("pyproject.toml", pyproject.to_owned()),
        ("uv.lock", LOCK_BEFORE.to_owned()),
    ]
}

/// A workspace with the shapes the tool must keep: comments, trailing comments, odd whitespace, single quotes,
/// nested groups, workspace sources, optional dependencies, excluded members, markers and extras.
fn workspace_fixture() -> Fixture {
    vec![
        (
            "pyproject.toml",
            r#"[project]
name = "root"
version = "0.1.0"
dependencies = [
    # HTTP client
    "httpx>=0.24.0",  # trailing comment
    "context",
    'Rich',
        "weird   >= 1.0 ,  <2 ; python_version>='3.8'" ,
    "pytest[cov]>=8.0; sys_platform == 'linux'",
]

[project.optional-dependencies]
cli = ["rich"]
empty = []

[dependency-groups]
dev = [
    "pytest>=8.0",
    { include-group = "lint" },
]
lint = ["pydantic~=2.0", "pydantic!=2.1"]

[tool.uv.sources]
context = { workspace = true }

[tool.uv.workspace]
members = ["packages/*"]
exclude = ["packages/seeds"]
"#
            .to_owned(),
        ),
        (
            "packages/context/pyproject.toml",
            "[project]\nname = \"context\"\nversion = \"0.1.0\"\ndependencies = [\n    \"pydantic==2.0.0\",\n    \"httpx\",\n    \"PyTest===9.0.1\",\n]\n"
                .to_owned(),
        ),
        (
            "packages/seeds/pyproject.toml",
            "[project]\nname = \"seeds\"\nversion = \"0.1.0\"\ndependencies = [\"httpx\"]\n".to_owned(),
        ),
        ("uv.lock", "version = 1\n".to_owned()),
    ]
}

fn workspace_lock() -> String {
    format!("{WORKSPACE_LOCK}\n[[package]]\nname = \"weird\"\nversion = \"1.5\"\n")
}

fn materialize(fixture: &Fixture) -> TempDir {
    let dir = tempfile::tempdir().unwrap();
    for (name, text) in fixture {
        write(&dir.path().join(name), text);
    }
    dir
}

fn outcome(program: &Path, args: &[&str], fixture: &Fixture, fake: &FakeUv) -> Outcome {
    let dir = materialize(fixture);
    fake.reset();
    let mut command = Command::new(program);
    command
        .args(args)
        .arg("--project")
        .arg(dir.path())
        .current_dir(dir.path());
    let output = run(fake.apply(&mut command));
    let root = dir.path().canonicalize().unwrap();
    let root_uri = uv_upx::path_uri::path_as_uri(&root);
    let normalize = |text: &str| {
        text.replace(&root_uri, "<ROOT>")
            .replace(&*root.to_string_lossy(), "<ROOT>")
    };
    let files = fixture
        .iter()
        .map(|(name, _)| ((*name).to_owned(), std::fs::read_to_string(dir.path().join(name)).ok()))
        .collect();
    Outcome {
        exit_code: output.status.code(),
        stdout: normalize(&stdout(&output)),
        logs: log_lines(&String::from_utf8_lossy(&output.stderr))
            .iter()
            .map(|line| normalize(line))
            .collect(),
        files,
        uv_calls: fake.commands(),
    }
}

/// Run both implementations and compare.
fn assert_parity(bin: Bin, args: &[&str], fixture: &Fixture, fake: &FakeUv) {
    let Some(python) = python_bin(bin) else {
        eprintln!(
            "skipped: the Python CLI is not in {}/.venv (run `uv sync`)",
            repo_root().display()
        );
        return;
    };
    let expected = outcome(&python, args, fixture, fake);
    let actual = outcome(&rust_bin(bin), args, fixture, fake);
    assert_eq!(actual, expected, "args: {args:?}");
    // A scenario that changes nothing would not prove much: the fixtures are chosen to produce output.
    assert!(
        !expected.logs.is_empty() || !expected.stdout.is_empty(),
        "the scenario produced no output"
    );
}

#[test]
fn upgrade_simple_project() {
    let fake = FakeUv::new(&lock_after());
    assert_parity(Bin::Short, &[], &simple_fixture(PYPROJECT), &fake);
    assert_parity(Bin::Full, &["upgrade", "run"], &simple_fixture(PYPROJECT), &fake);
}

#[test]
fn upgrade_no_sync_dry_run_verbose() {
    let fake = FakeUv::new(&lock_after());
    for args in [
        &["--no-sync"][..],
        &["--dry-run"],
        &["--verbose"],
        &["--dry-run", "--no-sync", "--verbose"],
    ] {
        assert_parity(Bin::Short, args, &simple_fixture(PYPROJECT), &fake);
    }
}

#[test]
fn upgrade_nothing_to_do() {
    let fake = FakeUv::new(&format!("{LOCK_BEFORE}\n# re-resolved\n"));
    assert_parity(Bin::Short, &["--no-sync"], &simple_fixture(PYPROJECT), &fake);
    assert_parity(Bin::Short, &[], &simple_fixture(PYPROJECT), &fake);
}

#[test]
fn upgrade_failures_roll_back() {
    let fake = FakeUv::new(&lock_after()).sync_fails();
    assert_parity(Bin::Short, &[], &simple_fixture(PYPROJECT), &fake);

    let fake = FakeUv::new(&lock_after()).lock_fails(1, "error: No solution found\n");
    assert_parity(Bin::Short, &["--no-sync"], &simple_fixture(PYPROJECT), &fake);
    assert_parity(Bin::Short, &[], &simple_fixture(PYPROJECT), &fake);
}

#[test]
fn upgrade_local_segments_fallback() {
    let fixture = simple_fixture(&PYPROJECT.replace("httpx>=0.24.0", "httpx>=0.24.0+cpu"));
    let fake = FakeUv::new(&lock_after())
        .lock_fails_once("error: Operator >= is incompatible with versions containing non-empty local segments\n");
    assert_parity(Bin::Short, &["--no-sync"], &fixture, &fake);
    assert_parity(Bin::Short, &[], &fixture, &fake);
}

#[test]
fn upgrade_keep_unconstrained_and_preserve_names() {
    let fake = FakeUv::new(&lock_after());
    let fixture = simple_fixture(&PYPROJECT.replace("\"httpx>=0.24.0\"", "\"HTTPx\""));
    assert_parity(Bin::Short, &["--keep-unconstrained"], &fixture, &fake);
    assert_parity(
        Bin::Short,
        &["--preserve-original-package-names", "--no-sync"],
        &fixture,
        &fake,
    );
    assert_parity(Bin::Short, &["--no-sync"], &fixture, &fake);
}

#[test]
fn upgrade_workspace_profiles() {
    let fake = FakeUv::new(&workspace_lock());
    for args in [
        &["--no-sync"][..],
        &["--no-sync", "--verbose"],
        &["--no-sync", "--keep-unconstrained"],
        &["--no-sync", "--profile", "with_pinned"],
        &["--profile", "with_pinned", "--verbose"],
        &["--dry-run", "--profile", "with_pinned"],
        &["--no-sync", "--preserve-original-package-names"],
    ] {
        assert_parity(Bin::Short, args, &workspace_fixture(), &fake);
    }
}

#[test]
fn helpers_collect() {
    let fake = FakeUv::new("");
    let collect = ["helpers", "collect-top-level-dependencies-from-project"];
    assert_parity(Bin::Full, &collect, &workspace_fixture(), &fake);
    assert_parity(
        Bin::Full,
        &[&collect[..], &["--only-special-cases"]].concat(),
        &workspace_fixture(),
        &fake,
    );
    assert_parity(
        Bin::Full,
        &[
            &collect[..],
            &["--only-special-cases", "--preserve-original-package-names"],
        ]
        .concat(),
        &workspace_fixture(),
        &fake,
    );
}

#[test]
fn errors_before_the_update() {
    let fake = FakeUv::new("");
    // No uv.lock: exit 1, nothing written (the messages differ: a traceback against one line).
    let fixture = vec![("pyproject.toml", PYPROJECT.to_owned())];
    assert_parity_loose(Bin::Short, &[], &fixture, &fake);
    // An invalid dependency string: exit 1 before any `uv` call.
    let fixture = simple_fixture(&PYPROJECT.replace("httpx>=0.24.0", "httpx @ https://example.com/x.whl"));
    assert_parity_loose(Bin::Short, &[], &fixture, &fake);
    let fixture = simple_fixture(&PYPROJECT.replace("httpx>=0.24.0", "httpx>=v1"));
    assert_parity_loose(Bin::Short, &[], &fixture, &fake);
}

/// Like [`assert_parity`], but the logs are not compared (Python prints a traceback there).
fn assert_parity_loose(bin: Bin, args: &[&str], fixture: &Fixture, fake: &FakeUv) {
    let Some(python) = python_bin(bin) else {
        eprintln!(
            "skipped: the Python CLI is not in {}/.venv (run `uv sync`)",
            repo_root().display()
        );
        return;
    };
    let mut expected = outcome(&python, args, fixture, fake);
    let mut actual = outcome(&rust_bin(bin), args, fixture, fake);
    expected.logs.clear();
    actual.logs.clear();
    assert_eq!(actual, expected, "args: {args:?}");
    assert_eq!(actual.exit_code, Some(1));
}

#[test]
fn version_output() {
    for bin in [Bin::Full, Bin::Short] {
        let Some(python) = python_bin(bin) else {
            return;
        };
        let expected = run(Command::new(python).arg("--version"));
        let actual = run(Command::new(rust_bin(bin)).arg("--version"));
        assert_eq!(stdout(&actual), stdout(&expected));
        assert_eq!(actual.status.code(), expected.status.code());
    }
}
