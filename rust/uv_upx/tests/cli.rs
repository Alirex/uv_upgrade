//! The CLI and the upgrade flow through the binaries, with a fake `uv`: the counterparts of the Python tests
//! `test_run_updater.py`, `test_updater.py` and `test_version.py`.

#![expect(
    clippy::unwrap_used,
    clippy::expect_used,
    reason = "a test panics on an unexpected value"
)]

mod common;

use common::{
    FakeUv, LOCK_BEFORE, MEMBER_PYPROJECT, PYPROJECT, ROOT_PYPROJECT, SYNC, SYNC_FROZEN, UPGRADE, WORKSPACE_LOCK,
    lock_after, log_lines, project, read, run, stderr, stdout, uv_upgrade, uv_upx, workspace,
};

fn upgrade_run(root: &std::path::Path, extra: &[&str]) -> std::process::Command {
    let mut command = uv_upx();
    command.args(["upgrade", "run", "--project"]).arg(root).args(extra);
    command
}

#[test]
fn version_of_both_binaries() {
    let expected = format!("uv-upx {}\n", env!("CARGO_PKG_VERSION"));
    for mut command in [uv_upx(), uv_upgrade()] {
        let output = run(command.arg("--version"));
        assert!(output.status.success());
        assert_eq!(stdout(&output), expected);
    }
    let output = run(uv_upx().args(["upgrade", "run", "--version"]));
    assert_eq!(stdout(&output), expected);
}

#[test]
fn version_matches_pyproject() {
    let pyproject = read(&std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../../pyproject.toml"));
    let line = pyproject
        .lines()
        .find(|line| line.starts_with("version = "))
        .expect("pyproject.toml has a version");
    assert_eq!(line, format!("version = \"{}\"", env!("CARGO_PKG_VERSION")));
}

#[test]
fn missing_command_is_a_usage_error() {
    let output = run(&mut uv_upx());
    assert_eq!(output.status.code(), Some(2));
    assert!(stderr(&output).contains("Missing command."));
    let output = run(uv_upx().arg("upgrade"));
    assert_eq!(output.status.code(), Some(2));
    let output = run(uv_upgrade().arg("--bogus"));
    assert_eq!(output.status.code(), Some(2));
}

#[test]
fn project_must_be_a_directory() {
    let output = run(uv_upgrade().args(["--project", "/nonexistent/path"]));
    assert_eq!(output.status.code(), Some(1));
    assert!(stderr(&output).contains("Path /nonexistent/path is not a directory."));
}

#[test]
fn missing_uv_lock_is_an_error() {
    let dir = tempfile::tempdir().unwrap();
    common::write(&dir.path().join("pyproject.toml"), PYPROJECT);
    let output = run(uv_upgrade().arg("--project").arg(dir.path()));
    assert_eq!(output.status.code(), Some(1));
    assert!(stderr(&output).contains("uv.lock does not exist."));
}

#[cfg(unix)]
mod with_fake_uv {
    use super::{
        FakeUv, LOCK_BEFORE, MEMBER_PYPROJECT, PYPROJECT, ROOT_PYPROJECT, SYNC, SYNC_FROZEN, UPGRADE, WORKSPACE_LOCK,
        lock_after, log_lines, project, read, run, stderr, upgrade_run, uv_upgrade, workspace,
    };

    #[test]
    fn upgrade_writes_pyproject_and_syncs() {
        let dir = project(PYPROJECT, LOCK_BEFORE);
        let fake = FakeUv::new(&lock_after());
        let output = run(fake.apply(uv_upgrade().arg("--project").arg(dir.path())));

        assert!(output.status.success(), "{}", stderr(&output));
        assert_eq!(
            read(&dir.path().join("pyproject.toml")),
            PYPROJECT.replace(">=0.24.0", ">=0.28.1")
        );
        assert_eq!(read(&dir.path().join("uv.lock")), lock_after());
        assert_eq!(fake.commands(), vec![UPGRADE, SYNC]);
        let logs = log_lines(&stderr(&output));
        assert!(
            logs.iter()
                .any(|line| line.ends_with("INFO -   httpx: >=0.24.0 -> >=0.28.1")),
            "{logs:?}"
        );
        assert_eq!(
            logs.last().unwrap(),
            "uv_upx.services.updater.finalize_updating - INFO - Synced dependencies successfully with updating uv.lock."
        );
    }

    #[test]
    fn no_sync_relocks_without_sync() {
        let dir = project(PYPROJECT, LOCK_BEFORE);
        let fake = FakeUv::new(&lock_after());
        let output = run(fake.apply(&mut upgrade_run(dir.path(), &["--no-sync"])));

        assert!(output.status.success());
        assert!(read(&dir.path().join("pyproject.toml")).contains(">=0.28.1"));
        assert_eq!(fake.commands(), vec![UPGRADE, "uv lock"]);
    }

    #[test]
    fn dry_run_restores_files() {
        let dir = project(PYPROJECT, LOCK_BEFORE);
        let fake = FakeUv::new(&lock_after());
        let output = run(fake.apply(&mut upgrade_run(dir.path(), &["--dry-run"])));

        assert!(output.status.success());
        assert_eq!(read(&dir.path().join("pyproject.toml")), PYPROJECT);
        assert_eq!(read(&dir.path().join("uv.lock")), LOCK_BEFORE);
        assert_eq!(fake.commands(), vec![UPGRADE, SYNC_FROZEN]);
        let logs = log_lines(&stderr(&output));
        assert_eq!(
            logs.last().unwrap(),
            "uv_upx.services.updater.run_updater - INFO - Dry run enabled, rolling back to previous state."
        );
    }

    #[test]
    fn nothing_to_upgrade_restores_lock() {
        let dir = project(PYPROJECT, LOCK_BEFORE);
        let fake = FakeUv::new(&format!("{LOCK_BEFORE}\n# re-resolved\n"));
        let output = run(fake.apply(&mut upgrade_run(dir.path(), &["--no-sync"])));

        assert!(output.status.success());
        assert_eq!(read(&dir.path().join("pyproject.toml")), PYPROJECT);
        assert_eq!(read(&dir.path().join("uv.lock")), LOCK_BEFORE);
        assert_eq!(fake.commands(), vec![UPGRADE]);
    }

    #[test]
    fn failed_sync_rolls_back() {
        let dir = project(PYPROJECT, LOCK_BEFORE);
        let fake = FakeUv::new(&lock_after()).sync_fails();
        let output = run(fake.apply(uv_upgrade().arg("--project").arg(dir.path())));

        // Like the Python version: the failure is logged and rolled back, the exit code stays 0.
        assert!(output.status.success());
        assert_eq!(read(&dir.path().join("pyproject.toml")), PYPROJECT);
        assert_eq!(read(&dir.path().join("uv.lock")), LOCK_BEFORE);
        assert_eq!(fake.commands(), vec![UPGRADE, SYNC, SYNC_FROZEN]);
        assert!(stderr(&output).contains("Failed to update dependencies: '<class 'uv_upx.services.run_uv_related.exceptions.UnresolvedDependencyError'>:Failed to sync dependencies with 'uv sync'. Please check your dependency specifications.' Rolling back to previous state."));
    }

    #[test]
    fn failed_lock_rolls_back() {
        let dir = project(PYPROJECT, LOCK_BEFORE);
        let fake = FakeUv::new(&lock_after()).lock_fails(1, "error: No solution found\n");
        let output = run(fake.apply(&mut upgrade_run(dir.path(), &["--no-sync"])));

        assert!(output.status.success());
        assert_eq!(read(&dir.path().join("pyproject.toml")), PYPROJECT);
        assert_eq!(read(&dir.path().join("uv.lock")), LOCK_BEFORE);
        // uv's stderr is shown to the user.
        assert!(stderr(&output).contains("error: No solution found\n"));
    }

    #[test]
    fn local_segments_fallback_pins_and_retries() {
        let pyproject = PYPROJECT.replace("httpx>=0.24.0", "httpx>=0.24.0+cpu");
        let dir = project(&pyproject, LOCK_BEFORE);
        let fake = FakeUv::new(&lock_after()).lock_fails_once(
            "error: Operator >= is incompatible with versions containing non-empty local segments (`+cpu`)\n",
        );
        let output = run(fake.apply(&mut upgrade_run(dir.path(), &["--no-sync"])));

        assert!(output.status.success(), "{}", stderr(&output));
        // Rollback, pin with `==`, lock again, then the in-memory `>=` moves to the new version.
        assert_eq!(fake.commands(), vec![UPGRADE, UPGRADE, "uv lock"]);
        assert_eq!(
            read(&dir.path().join("pyproject.toml")),
            PYPROJECT.replace(">=0.24.0", ">=0.28.1")
        );
        assert!(
            stderr(&output).contains("Cannot proceed with pinned profile because there are local segments present.")
        );
    }

    #[test]
    fn cli_keep_unconstrained() {
        let pyproject = PYPROJECT.replace("\"httpx>=0.24.0\"", "\"httpx\"");
        let dir = project(&pyproject, LOCK_BEFORE);
        let fake = FakeUv::new(&lock_after());
        let output = run(fake.apply(&mut upgrade_run(dir.path(), &["--keep-unconstrained"])));

        assert!(output.status.success(), "{}", stderr(&output));
        assert_eq!(read(&dir.path().join("pyproject.toml")), pyproject);
    }

    #[test]
    fn cli_dry_run() {
        let dir = project(PYPROJECT, LOCK_BEFORE);
        let fake = FakeUv::new(&lock_after());
        let output = run(fake.apply(&mut upgrade_run(dir.path(), &["--dry-run"])));

        assert!(output.status.success(), "{}", stderr(&output));
        assert_eq!(read(&dir.path().join("pyproject.toml")), PYPROJECT);
        assert_eq!(fake.commands(), vec![UPGRADE, SYNC_FROZEN]);
    }

    #[test]
    fn verbose_lists_the_files() {
        let (dir, _) = workspace();
        let fake = FakeUv::new(WORKSPACE_LOCK);
        let output = run(fake.apply(&mut upgrade_run(dir.path(), &["--verbose", "--no-sync"])));

        assert!(output.status.success(), "{}", stderr(&output));
        let logs = log_lines(&stderr(&output));
        assert_eq!(
            logs[0],
            "uv_upx.services.updater.run_updater - INFO - Found 2 pyproject.toml files in the workspace."
        );
        assert!(logs[1].ends_with("/pyproject.toml"));
        assert!(logs[2].ends_with("/packages/context/pyproject.toml"));
    }

    /// The sorted change lines that the updater logged.
    fn logged_changes(text: &str) -> Vec<String> {
        let mut changes: Vec<String> = log_lines(text)
            .into_iter()
            .filter_map(|line| {
                line.strip_prefix("uv_upx.services.dependency_up.handle_groups - INFO -   ")
                    .map(ToOwned::to_owned)
            })
            .collect();
        changes.sort();
        changes
    }

    #[test]
    fn upgrade_workspace() {
        let (dir, member) = workspace();
        let fake = FakeUv::new(WORKSPACE_LOCK);
        let output = run(fake.apply(&mut upgrade_run(dir.path(), &["--no-sync"])));

        assert!(output.status.success(), "{}", stderr(&output));
        assert_eq!(
            logged_changes(&stderr(&output)),
            vec![
                "httpx:  -> >=0.28.1",
                "httpx: >=0.24.0 -> >=0.28.1",
                "pytest: >=8.0 -> >=9.0.1",
                "rich:  -> >=14.2.0",
            ]
        );
        // Workspace member "context" is untouched, comments and nested groups are kept.
        assert_eq!(
            read(&dir.path().join("pyproject.toml")),
            ROOT_PYPROJECT
                .replace("\"httpx>=0.24.0\"", "\"httpx>=0.28.1\"")
                .replace("[\"rich\"]", "[\"rich>=14.2.0\"]")
                .replace("\"pytest>=8.0\"", "\"pytest>=9.0.1\"")
        );
        // Pinned versions are kept with the default profile.
        assert_eq!(
            read(&member.join("pyproject.toml")),
            MEMBER_PYPROJECT.replace("\"httpx\"", "\"httpx>=0.28.1\"")
        );
    }

    #[test]
    fn upgrade_workspace_keep_unconstrained() {
        let (dir, member) = workspace();
        let fake = FakeUv::new(WORKSPACE_LOCK);
        let output = run(fake.apply(&mut upgrade_run(dir.path(), &["--no-sync", "--keep-unconstrained"])));

        assert!(output.status.success(), "{}", stderr(&output));
        // "rich" and the member's "httpx" have no constraint: they are left alone.
        assert_eq!(
            logged_changes(&stderr(&output)),
            vec!["httpx: >=0.24.0 -> >=0.28.1", "pytest: >=8.0 -> >=9.0.1"]
        );
        assert_eq!(
            read(&dir.path().join("pyproject.toml")),
            ROOT_PYPROJECT
                .replace("\"httpx>=0.24.0\"", "\"httpx>=0.28.1\"")
                .replace("\"pytest>=8.0\"", "\"pytest>=9.0.1\"")
        );
        assert_eq!(read(&member.join("pyproject.toml")), MEMBER_PYPROJECT);
    }

    #[test]
    fn upgrade_workspace_with_pinned() {
        let (dir, member) = workspace();
        let fake = FakeUv::new(WORKSPACE_LOCK);
        let output = run(fake.apply(&mut upgrade_run(dir.path(), &["--no-sync", "--profile", "with_pinned"])));

        assert!(output.status.success(), "{}", stderr(&output));
        let member_text = read(&member.join("pyproject.toml"));
        assert!(member_text.contains("\"pydantic==2.12.5\""), "{member_text}");
        // The pinned profile deletes uv.lock before relocking, so `uv lock` runs without `--upgrade` at the end.
        assert_eq!(fake.commands(), vec![UPGRADE, "uv lock"]);
    }
}

mod help_snapshots {
    use super::{run, stdout, uv_upgrade, uv_upx};

    #[test]
    fn help_texts() {
        insta::assert_snapshot!("uv_upx_help", stdout(&run(uv_upx().arg("--help"))));
        insta::assert_snapshot!("uv_upgrade_help", stdout(&run(uv_upgrade().arg("--help"))));
        insta::assert_snapshot!(
            "upgrade_run_help",
            stdout(&run(uv_upx().args(["upgrade", "run", "--help"])))
        );
        insta::assert_snapshot!("helpers_help", stdout(&run(uv_upx().args(["helpers", "--help"]))));
        insta::assert_snapshot!(
            "collect_help",
            stdout(&run(uv_upx().args([
                "helpers",
                "collect-top-level-dependencies-from-project",
                "--help"
            ])))
        );
    }
}

#[test]
fn helpers_collect_prints_special_cases() {
    let (dir, _) = workspace();
    let output = run(uv_upx()
        .args([
            "helpers",
            "collect-top-level-dependencies-from-project",
            "--only-special-cases",
            "--project",
        ])
        .arg(dir.path()));
    assert!(output.status.success(), "{}", stderr(&output));
    let root_uri = uv_upx::path_uri::path_as_uri(&dir.path().join("pyproject.toml"));
    let member_uri = uv_upx::path_uri::path_as_uri(&dir.path().join("packages/context/pyproject.toml"));
    assert_eq!(
        stdout(&output),
        format!(
            "{root_uri}\n  project.dependencies:\n    context\n----------\n  project.optional-dependencies[cli]:\n    rich\n----------\n====================\n\
             {member_uri}\n  project.dependencies:\n    pydantic==2.0.0\n    httpx\n----------\n====================\n"
        )
    );
    let logs = log_lines(&stderr(&output));
    assert_eq!(
        logs.first().unwrap(),
        "uv_upx.services.collect_top_level_dependencies.collect_top_level_dependencies - INFO - Collecting top level dependencies..."
    );
    assert_eq!(
        logs.last().unwrap(),
        "uv_upx.services.collect_top_level_dependencies.collect_top_level_dependencies - INFO - Done."
    );

    // Without the flag nothing is listed (the Python version behaves the same).
    let output = run(uv_upx()
        .args(["helpers", "collect-top-level-dependencies-from-project", "--project"])
        .arg(dir.path()));
    assert!(output.status.success());
    assert_eq!(stdout(&output), "");
}
