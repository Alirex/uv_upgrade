use crate::services::run_uv_related::run_uv_lock::run_uv_lock;

pub async fn update_lock_file(
    project_root_path: std::path::PathBuf,
) -> Result<(), Box<dyn std::error::Error>> {
    // Because we want a fast update. Without triggering build for now.
    run_uv_lock(
        &project_root_path,
        true,
    )
    .await?;

    Ok(())
}