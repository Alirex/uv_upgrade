use crate::services::run_uv_related::errors::RunUvRelatedError;
use async_process::Command;
use std::path::PathBuf;
use tracing::{error, info};

#[derive(Debug, Clone, Copy)]
pub enum UvSyncMode {
    Upgrade,
    Frozen,
    Default,
}

// include_all=true
pub async fn run_uv_sync(
    workdir: &PathBuf,
    uv_sync_mode: UvSyncMode,
    include_all: bool,
) -> Result<(), RunUvRelatedError> {
    let mut command = Command::new("uv");
    command.arg("sync");

    if include_all {
        command.args(["--all-groups", "--all-extras", "--all-packages"]);
    }

    match uv_sync_mode {
        UvSyncMode::Upgrade => {
            command.arg("--upgrade");
        }
        UvSyncMode::Frozen => {
            command.arg("--frozen");
        }
        UvSyncMode::Default => {}
    }

    command.current_dir(workdir);

    info!(?command, "Running 'uv sync' command.");

    let output = command.output().await.map_err(|e| {
        RunUvRelatedError::CommandExecutionError(format!("Failed to execute command: {}", e))
    })?;

    if !output.status.success() {
        let error_message = String::from_utf8_lossy(&output.stderr);
        error!(?error_message, "Command 'uv sync' failed with error");

        return Err(RunUvRelatedError::UnresolvedDependency(format!(
            "Failed to sync dependencies with 'uv sync'. Please check your dependency specifications. Error: {}",
            error_message
        )));
    }

    Ok(())
}
