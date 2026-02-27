use tracing::info;
use crate::services::normalize_paths::get_and_check_path_to_uv_lock;
use crate::services::run_uv_related::run_uv_lock::run_uv_lock;
use crate::services::run_uv_related::run_uv_sync::{UvSyncMode, run_uv_sync};
use crate::services::upgrade_profile::upgrade_profile_enum::UpgradeProfile;

pub async fn finalize_updating(
    project_root_path: std::path::PathBuf,
    dry_run: bool,
    no_sync: bool,
    profile: UpgradeProfile,
    interactive: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    if dry_run {
        info!("Dry run. No changes were made.");
        return Ok(());
    }

    if profile == UpgradeProfile::WithPinned || interactive {
        let uv_lock_path = get_and_check_path_to_uv_lock(&project_root_path).await?;
        tokio::fs::remove_file(uv_lock_path).await.ok();
    }

    if no_sync {
        run_uv_lock(&project_root_path, false).await?;
        info!("Updated uv.lock successfully.");
    } else {
        // Because we want to re-check that all is ok.
        run_uv_sync(&project_root_path, UvSyncMode::Default, true).await?;
        info!("Synced dependencies successfully with updating uv.lock.");
    }

    Ok(())
}
