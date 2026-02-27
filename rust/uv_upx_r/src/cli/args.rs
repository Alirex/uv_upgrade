use std::path::PathBuf;

use crate::services::upgrade_profile::upgrade_profile_enum::UpgradeProfile;
use clap::{Args, Parser, Subcommand};

#[derive(Parser, Debug)]
#[command(long_about = None)]
#[command(version, propagate_version = true)]
// #[command(version = concat!(env!("CARGO_PKG_NAME"), " ", env!("CARGO_PKG_VERSION")))]
#[command(styles = clap_cargo::style::CLAP_STYLING)]
#[command(name = "uv-upx")]
#[command(about = "Update pyproject.toml dependencies to latest compatible versions.")]
pub struct Cli {
    #[command(subcommand)]
    pub command: CommandsTop,
}

#[derive(Subcommand, Debug)]
pub enum CommandsTop {
    /// 1 Update pyproject.toml dependencies to latest compatible versions.
    Upgrade(UpgradeArgs),

    /// CLI Helpers
    CliHelpers(CliHelpersArgs),
}

#[derive(Debug, Args)]
pub struct UpgradeArgs {
    /// Path to the project root directory. Use the current working directory if not specified.
    #[arg(short = 'p', long = "project", value_name = "PATH")]
    pub project_root_path: Option<PathBuf>,

    /// Show more output
    #[arg(long = "verbose")]
    pub verbose: bool,

    // [extra]-[BEGIN]
    /// Preserve original package names in pyproject.toml
    #[arg(long = "preserve-original-package-names")]
    pub preserve_original_package_names: bool,

    /// Do not run uv-sync.
    #[arg(long = "no-sync")]
    pub no_sync: bool,
    // [extra]-[END]
    /// Which profile to use when upgrading dependencies. (Experimental feature)
    #[arg(long = "profile")]
    pub profile: Option<UpgradeProfile>,

    /// Enable interactive mode for selecting updates. (Experimental feature)
    #[arg(long = "interactive")]
    pub interactive: bool,
}

#[derive(Args, Debug)]
pub struct CliHelpersArgs {
    #[command(subcommand)]
    pub command: CliHelpersCommands,
}

#[derive(Subcommand, Debug)]
pub enum CliHelpersCommands {
    /// Export cli help as Markdown.
    ExportCliHelp(ExportCliHelpArgs),

    /// Generate shell completion.
    GenerateShellCompletion(GenerateShellCompletionArgs),
}

#[derive(Debug, Args)]
pub struct ExportCliHelpArgs {
    /// Path to the output file.
    #[arg(long = "output", value_name = "PATH")]
    pub output: PathBuf,
}

#[derive(Args, Debug)]
pub struct GenerateShellCompletionArgs {
    #[arg(value_enum)]
    pub shell: clap_complete_command::Shell,
}

#[cfg(test)]
mod tests;
