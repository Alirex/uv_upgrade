//! `uv-upx`: upgrade the dependency constraints in the `pyproject.toml` files of uv projects and workspaces.
//!
//! A port of the Python package in `src/uv_upx` with the same behaviour: the commands, flags, log lines and the
//! resulting files are meant to be identical (the parity tests in `tests/parity.rs` check it against the Python CLI).

pub mod cli;
pub mod collect;
pub mod completion;
pub mod dependency;
pub mod error;
pub mod helpers;
pub mod interactive;
pub mod logging;
pub mod package_name;
pub mod path_uri;
pub mod paths;
pub mod pinned;
pub mod pyprojects;
pub mod toml_access;
pub mod updater;
pub mod uv_lock;
pub mod uv_runner;
pub mod uv_tool_config;

/// The distribution name: shown by `--version` of both binaries.
pub const APP_NAME: &str = "uv-upx";

/// The version of the crate (kept in step with `pyproject.toml`).
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Which dependencies an upgrade may change.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum UpgradeProfile {
    /// Only lower bounds (`>=`) move.
    #[default]
    Default,
    /// Also "pinned" (`==` exact version) dependencies move.
    WithPinned,
}

impl UpgradeProfile {
    /// The name as the `--profile` option takes it.
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Default => "default",
            Self::WithPinned => "with_pinned",
        }
    }
}

// By hand (not derived), so that the doc comments above do not become clap help text: Typer shows the values only.
impl clap::ValueEnum for UpgradeProfile {
    fn value_variants<'a>() -> &'a [Self] {
        &[Self::Default, Self::WithPinned]
    }

    fn to_possible_value(&self) -> Option<clap::builder::PossibleValue> {
        Some(clap::builder::PossibleValue::new(self.as_str()))
    }
}
