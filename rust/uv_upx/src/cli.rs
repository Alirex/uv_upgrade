//! The two command lines: `uv-upx` (commands `upgrade run` and `helpers ...`) and the short `uv-upgrade`
//! (`upgrade run` alone). Options and help texts copy the Typer apps.

use std::ffi::OsString;
use std::path::PathBuf;
use std::process::ExitCode;

use clap::{ArgAction, Args, CommandFactory, Parser, Subcommand};

use crate::error::Result;
use crate::helpers::{CollectTopLevelOptions, collect_top_level_dependencies};
use crate::paths::normalize_and_check_path_to_project_root;
use crate::updater::{UpdaterOptions, run_updater};
use crate::{APP_NAME, UpgradeProfile, VERSION, completion};

const PROJECT_HELP: &str = "Path to project root directory. Use current working directory if not specified.";
const PRESERVE_NAMES_HELP: &str = "Preserve original package names in pyproject.toml";
const NO_SYNC_HELP: &str = "Do not run uv-sync. In case of the complex build process. But, recommended to run with \
                            sync, for better chances for revealing problems.";
const KEEP_UNCONSTRAINED_HELP: &str = "Leave dependencies written without a version constraint (like `bla`) as they \
                                       are. By default they get a lower bound at the locked version.";

/// `--help` as Typer shows it (no `-h`).
#[derive(Args, Debug)]
pub struct HelpFlag {
    #[arg(long, action = ArgAction::Help, help = "Show this message and exit.")]
    help: Option<bool>,
}

/// `--install-completion` and `--show-completion` of a root command.
#[derive(Args, Debug)]
pub struct CompletionFlags {
    #[arg(long, help = "Install completion for the current shell.")]
    install_completion: bool,

    #[arg(
        long,
        help = "Show completion for the current shell, to copy it or customize the installation."
    )]
    show_completion: bool,
}

/// The options of `upgrade run` (and of the whole `uv-upgrade`).
#[derive(Args, Debug)]
#[expect(clippy::struct_excessive_bools, reason = "one independent CLI flag per field")]
pub struct RunArgs {
    #[arg(short = 'p', long = "project", value_name = "PATH", help = PROJECT_HELP)]
    project_root_path: Option<PathBuf>,

    /// Show changes without writing file
    #[arg(long)]
    dry_run: bool,

    /// Show more output
    #[arg(long)]
    verbose: bool,

    #[arg(long, help = PRESERVE_NAMES_HELP)]
    preserve_original_package_names: bool,

    #[arg(long, help = NO_SYNC_HELP)]
    no_sync: bool,

    #[arg(
        long,
        value_enum,
        value_name = "[default|with_pinned]",
        hide_possible_values = true,
        help = "Which profile to use when upgrading dependencies. (Experimental feature)"
    )]
    profile: Option<UpgradeProfile>,

    /// Enable interactive mode for selecting updates. (Experimental feature)
    #[arg(long)]
    interactive: bool,

    #[arg(long, help = KEEP_UNCONSTRAINED_HELP)]
    keep_unconstrained: bool,

    #[arg(long, help = "Show version and exit.")]
    version: bool,
}

impl RunArgs {
    fn run(&self) -> Result<()> {
        if self.version {
            print_version();
            return Ok(());
        }
        let project_root_path = normalize_and_check_path_to_project_root(self.project_root_path.as_deref())?;
        run_updater(
            &project_root_path,
            UpdaterOptions {
                dry_run: self.dry_run,
                verbose: self.verbose,
                preserve_original_package_names: self.preserve_original_package_names,
                no_sync: self.no_sync,
                interactive: self.interactive,
                keep_unconstrained: self.keep_unconstrained,
                profile: self.profile.unwrap_or_default(),
            },
        )
    }
}

/// The options of `helpers collect-top-level-dependencies-from-project`.
#[derive(Args, Debug)]
pub struct CollectArgs {
    #[arg(short = 'p', long = "project", value_name = "PATH", help = PROJECT_HELP)]
    project_root_path: Option<PathBuf>,

    /// Collect only complex and unhandled dependencies
    #[arg(long)]
    only_special_cases: bool,

    #[arg(long, help = PRESERVE_NAMES_HELP)]
    preserve_original_package_names: bool,

    #[command(flatten)]
    help: HelpFlag,
}

impl CollectArgs {
    fn run(&self) -> Result<()> {
        let project_root_path = normalize_and_check_path_to_project_root(self.project_root_path.as_deref())?;
        collect_top_level_dependencies(
            &project_root_path,
            CollectTopLevelOptions {
                only_special_cases: self.only_special_cases,
                preserve_original_package_names: self.preserve_original_package_names,
            },
            &mut std::io::stdout().lock(),
        )
    }
}

/// `uv-upx upgrade ...`
#[derive(Subcommand, Debug)]
pub enum UpgradeCommand {
    /// `uv-upx upgrade run`.
    #[command(about = "Update pyproject.toml dependencies to latest compatible versions.")]
    Run {
        /// The options.
        #[command(flatten)]
        args: RunArgs,
        /// `--help`.
        #[command(flatten)]
        help: HelpFlag,
    },
}

/// `uv-upx helpers ...`
#[derive(Subcommand, Debug)]
pub enum HelpersCommand {
    /// `uv-upx helpers collect-top-level-dependencies-from-project`.
    #[command(about = "Collect top-level dependencies from the project.")]
    CollectTopLevelDependenciesFromProject(CollectArgs),
}

/// The commands of `uv-upx`.
#[derive(Subcommand, Debug)]
pub enum FullCommand {
    /// Upgrade the dependencies.
    #[command(subcommand_required = true, about = None)]
    Upgrade {
        /// The command.
        #[command(subcommand)]
        command: UpgradeCommand,
        /// `--help`.
        #[command(flatten)]
        help: HelpFlag,
    },
    /// Helpers around the dependencies.
    #[command(subcommand_required = true, about = None)]
    Helpers {
        /// The command.
        #[command(subcommand)]
        command: HelpersCommand,
        /// `--help`.
        #[command(flatten)]
        help: HelpFlag,
    },
}

/// `uv-upx`: the full CLI.
#[derive(Parser, Debug)]
#[command(
    name = "uv-upx",
    about = "Upgrade dependencies in uv projects.",
    disable_help_flag = true,
    disable_version_flag = true,
    disable_help_subcommand = true
)]
pub struct FullCli {
    #[arg(long, help = "Show version and exit.")]
    version: bool,

    #[command(flatten)]
    completion: CompletionFlags,

    #[command(flatten)]
    help: HelpFlag,

    #[command(subcommand)]
    command: Option<FullCommand>,
}

/// `uv-upgrade`: `upgrade run` as the whole program.
#[derive(Parser, Debug)]
#[command(
    name = "uv-upgrade",
    about = "Update pyproject.toml dependencies to latest compatible versions.",
    disable_help_flag = true,
    disable_version_flag = true
)]
pub struct ShortCli {
    #[command(flatten)]
    run: RunArgs,

    #[command(flatten)]
    completion: CompletionFlags,

    #[command(flatten)]
    help: HelpFlag,
}

fn print_version() {
    println!("{APP_NAME} {VERSION}");
}

fn report(result: Result<()>) -> ExitCode {
    match result {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("Error: {error}");
            ExitCode::FAILURE
        }
    }
}

fn parse<T: Parser>(args: impl IntoIterator<Item = OsString>) -> std::result::Result<T, ExitCode> {
    T::try_parse_from(args).map_err(|error| {
        // clap prints help and version to stdout with exit 0, usage errors to stderr with exit 2 (like Typer).
        let _ = error.print();
        ExitCode::from(u8::try_from(error.exit_code()).unwrap_or(2))
    })
}

fn handle_completion(flags: &CompletionFlags, command: &mut clap::Command) -> Option<ExitCode> {
    if flags.show_completion {
        return Some(report(completion::show_completion(command)));
    }
    if flags.install_completion {
        return Some(report(completion::install_completion(command)));
    }
    None
}

/// Run `uv-upx` with the given arguments (the first one is the program name).
#[must_use]
pub fn main_full(args: impl IntoIterator<Item = OsString>) -> ExitCode {
    let cli = match parse::<FullCli>(args) {
        Ok(cli) => cli,
        Err(code) => return code,
    };
    if cli.version {
        print_version();
        return ExitCode::SUCCESS;
    }
    if let Some(code) = handle_completion(&cli.completion, &mut FullCli::command()) {
        return code;
    }
    let Some(command) = cli.command else {
        // Typer: usage, then "Missing command.", exit 2.
        let _ = FullCli::command().print_help();
        eprintln!("Missing command.");
        return ExitCode::from(2);
    };
    report(match command {
        FullCommand::Upgrade {
            command: UpgradeCommand::Run { args, .. },
            ..
        } => args.run(),
        FullCommand::Helpers {
            command: HelpersCommand::CollectTopLevelDependenciesFromProject(args),
            ..
        } => args.run(),
    })
}

/// Run `uv-upgrade` with the given arguments (the first one is the program name).
#[must_use]
pub fn main_short(args: impl IntoIterator<Item = OsString>) -> ExitCode {
    let cli = match parse::<ShortCli>(args) {
        Ok(cli) => cli,
        Err(code) => return code,
    };
    if let Some(code) = handle_completion(&cli.completion, &mut ShortCli::command()) {
        return code;
    }
    report(cli.run.run())
}

#[cfg(test)]
mod tests {
    use clap::CommandFactory;

    use super::{FullCli, ShortCli};

    #[test]
    fn clap_definitions_are_consistent() {
        FullCli::command().debug_assert();
        ShortCli::command().debug_assert();
    }
}
