use crate::services::get_all_pyprojects::models::PyProjectWrapper;
use crate::services::run_uv_related::run_uv_sync::{UvSyncMode, run_uv_sync};
use crate::services::toml::{TomlDocumentMut, toml_save};
use std::path::PathBuf;
use tracing::info;

#[derive(Debug, Clone)]
pub struct UvLockWrapper {
    pub path: PathBuf,
    pub data: TomlDocumentMut,
}

#[derive(Debug, Clone)]
pub struct RollbackData {
    pub uv_lock: UvLockWrapper,
    pub py_projects: Vec<PyProjectWrapper>,
}

impl RollbackData {
    pub fn from_parts(
        uv_lock_path: PathBuf,
        uv_lock_data: TomlDocumentMut,
        py_projects: Vec<PyProjectWrapper>,
    ) -> Self {
        let uv_lock_wrapper = UvLockWrapper {
            path: uv_lock_path,
            // TODO: Rework to not use clone
            data: uv_lock_data.clone(),
        };

        Self {
            uv_lock: uv_lock_wrapper,
            py_projects,
        }
    }
}

pub async fn rollback_updater(
    rollback_data: &RollbackData,
    no_sync: bool,
) -> Result<(), std::io::Error> {
    toml_save(&rollback_data.uv_lock.path, &rollback_data.uv_lock.data).await?;

    for py_project in &rollback_data.py_projects {
        toml_save(&py_project.path, &py_project.data).await?;
    }

    if !no_sync {
        run_uv_sync(
            &rollback_data.uv_lock.path.parent().unwrap().to_path_buf(),
            UvSyncMode::Frozen,
            true,
        )
        .await
        .map_err(|e| std::io::Error::other(format!("{}", e)))?;
    }

    info!("Rollback completed.");

    Ok(())
}
