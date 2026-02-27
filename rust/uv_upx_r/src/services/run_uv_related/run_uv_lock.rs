use crate::services::local_segments::constants::ERROR_TEXT_PART_I_NON_EMPTY_LOCAL_SEGMENT;
use crate::services::run_uv_related::errors::RunUvRelatedError;
use async_process::Command;
use std::path::PathBuf;
use tracing::{error, info};

// upgrade=false
pub async fn run_uv_lock(workdir: &PathBuf, upgrade: bool) -> Result<(), RunUvRelatedError> {
    let mut command = Command::new("uv");
    command.arg("lock");

    if upgrade {
        command.arg("--upgrade");
    }

    command.current_dir(workdir);

    info!(?command, "Running 'uv lock' command.");

    let output = command.output().await.map_err(|e| {
        RunUvRelatedError::CommandExecutionError(format!("Failed to execute command: {}", e))
    })?;

    if !output.status.success() {
        let error_message = String::from_utf8_lossy(&output.stderr);

        return if error_message.contains(ERROR_TEXT_PART_I_NON_EMPTY_LOCAL_SEGMENT) {
            error!(
                ?error_message,
                "Command 'uv lock' failed due to non-empty local segments"
            );
            Err(RunUvRelatedError::NonEmptyLocalSegments(
                "Failed to resolve dependencies with 'uv lock' due to non-empty local segments. Please check your dependency specifications.".to_string(),
            ))
        } else {
            error!(?error_message, "Command 'uv lock' failed with error");
            Err(RunUvRelatedError::UnresolvedDependency(format!(
                "Failed to resolve dependencies with 'uv lock'. Please check your dependency specifications. Error: {}",
                error_message
            )))
        };
    }

    Ok(())
}
