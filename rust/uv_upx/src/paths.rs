//! The project paths: root directory, `pyproject.toml`, `uv.lock`.

use std::path::{Path, PathBuf};

use crate::error::{Error, Result};

/// File name of a project file.
pub const NAME_OF_PYPROJECT_FILE: &str = "pyproject.toml";

/// File name of the uv lock file.
pub const NAME_OF_UV_LOCK_FILE: &str = "uv.lock";

/// The project root: the given path (made absolute) or the current directory.
///
/// # Errors
///
/// `Error::NotADirectory` when the path is not a directory.
pub fn normalize_and_check_path_to_project_root(path: Option<&Path>) -> Result<PathBuf> {
    let path = match path {
        Some(path) if path.is_absolute() => path.to_path_buf(),
        Some(path) => current_dir()?.join(path),
        None => current_dir()?,
    };
    if !path.is_dir() {
        return Err(Error::NotADirectory(path));
    }
    Ok(path)
}

fn current_dir() -> Result<PathBuf> {
    std::env::current_dir().map_err(|source| Error::Io {
        action: "Failed to read the current directory",
        path: PathBuf::from("."),
        source,
    })
}

fn get_and_check(root: &Path, name: &str) -> Result<PathBuf> {
    let path = root.join(name);
    if !path.exists() {
        return Err(Error::NotFound(path));
    }
    Ok(path)
}

/// `<root>/pyproject.toml`, which must exist.
///
/// # Errors
///
/// `Error::NotFound` when the file is missing.
pub fn get_and_check_path_to_pyproject(root: &Path) -> Result<PathBuf> {
    get_and_check(root, NAME_OF_PYPROJECT_FILE)
}

/// `<root>/uv.lock`, which must exist.
///
/// # Errors
///
/// `Error::NotFound` when the file is missing.
pub fn get_and_check_path_to_uv_lock(root: &Path) -> Result<PathBuf> {
    get_and_check(root, NAME_OF_UV_LOCK_FILE)
}
