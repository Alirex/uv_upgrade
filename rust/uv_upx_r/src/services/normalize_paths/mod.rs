use std::path::{Path, PathBuf};

const NAME_OF_PYPROJECT_FILE: &str = "pyproject.toml";
const NAME_OF_UV_LOCK_FILE: &str = "uv.lock";

pub async fn normalize_and_check_path_to_project_root(
    path: Option<&Path>,
) -> Result<PathBuf, std::io::Error> {
    match path {
        None => Ok(std::env::current_dir()?),
        Some(path) => {
            if !path.is_dir() {
                let msg = format!("Path {} is not a directory.", path.display());
                Err(std::io::Error::new(std::io::ErrorKind::NotADirectory, msg))
            } else {
                return_file_path_if_exists(path.to_path_buf())
            }
        }
    }
}

pub async fn get_and_check_path_to_pyproject(path: &Path) -> Result<PathBuf, std::io::Error> {
    let path = path.join(NAME_OF_PYPROJECT_FILE);

    return_file_path_if_exists(path)
}

pub async fn get_and_check_path_to_uv_lock(path: &Path) -> Result<PathBuf, std::io::Error> {
    let path = path.join(NAME_OF_UV_LOCK_FILE);

    return_file_path_if_exists(path)
}

fn return_file_path_if_exists(path: PathBuf) -> Result<PathBuf, std::io::Error> {
    if path.exists() {
        Ok(path)
    } else {
        Err(std::io::Error::new(
            std::io::ErrorKind::NotFound,
            format!("Path {} does not exist.", path.display()),
        ))
    }
}
