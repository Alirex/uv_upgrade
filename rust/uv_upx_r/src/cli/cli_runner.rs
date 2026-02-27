use crate::cli::args::{Cli, CliHelpersCommands, CommandsTop};
use crate::helpers::write_help_as_markdown::write_help_as_markdown;
use crate::logging::init::init_logging;
use crate::services::updater::run_updater::run_updater;
use app_root_folder::{get_app_root_folder_by_executable, get_executable_path};
use clap::{CommandFactory, Parser};
use std::io::stdout;

pub async fn cli_runner() {
    let _log_guard = init_logging();

    let executable_path = get_executable_path();
    let _app_root_folder = get_app_root_folder_by_executable(&executable_path);

    let cli = Cli::parse();

    match cli.command {
        CommandsTop::Upgrade(upgrade_args) => run_updater(upgrade_args.into()).await.unwrap(),
        CommandsTop::CliHelpers(cli_helpers_args) => match cli_helpers_args.command {
            CliHelpersCommands::ExportCliHelp(args) => {
                write_help_as_markdown::<Cli>(&args.output).await;
            }
            CliHelpersCommands::GenerateShellCompletion(args) => {
                args.shell.generate(&mut Cli::command(), &mut stdout());
            }
        },
    }
}
