//! Find and load all `pyproject.toml` files of a project: the root and the uv workspace members.

use std::collections::BTreeSet;
use std::path::{Path, PathBuf};

use toml_edit::DocumentMut;

use crate::error::{Result, read_text, write_text};
use crate::logging;
use crate::path_uri::path_as_uri;
use crate::paths::{NAME_OF_PYPROJECT_FILE, get_and_check_path_to_pyproject};
use crate::toml_access::toml_parse;
use crate::uv_tool_config::read_uv_tool_config;

const LOGGER_GLOBS: &str = "uv_upx.services.get_all_pyprojects.get_pyproject_paths_by_globs";

/// One loaded `pyproject.toml`: the editable document and the text it was read from (for the rollback).
#[derive(Clone, Debug)]
pub struct PyProject {
    /// The file.
    pub path: PathBuf,
    /// The text as read.
    pub original_text: String,
    /// The document; edits keep the formatting and comments.
    pub doc: DocumentMut,
}

impl PyProject {
    /// Load a file.
    ///
    /// # Errors
    ///
    /// When the file cannot be read or is not valid TOML.
    pub fn load(path: PathBuf) -> Result<Self> {
        let original_text = read_text(&path)?;
        let doc = toml_parse(&original_text, &path)?;
        Ok(Self {
            path,
            original_text,
            doc,
        })
    }

    /// Write the document back to its file.
    ///
    /// # Errors
    ///
    /// When the file cannot be written.
    pub fn save(&self) -> Result<()> {
        write_text(&self.path, &self.doc.to_string())
    }

    /// Write the original text back to the file.
    ///
    /// # Errors
    ///
    /// When the file cannot be written.
    pub fn restore(&self) -> Result<()> {
        write_text(&self.path, &self.original_text)
    }
}

/// The `pyproject.toml` files that the patterns name: a matching file named `pyproject.toml`, or the `pyproject.toml`
/// inside a matching directory.
#[must_use]
pub fn get_pyproject_paths_by_globs(base_path: &Path, patterns: &[String]) -> BTreeSet<PathBuf> {
    let mut paths = BTreeSet::new();
    let base = glob::Pattern::escape(&base_path.to_string_lossy());
    for pattern in patterns {
        let Ok(entries) = glob::glob(&format!("{base}/{pattern}")) else {
            continue;
        };
        for path in entries.flatten() {
            if path.is_file() {
                if path.file_name().is_some_and(|name| name == NAME_OF_PYPROJECT_FILE) {
                    paths.insert(path);
                }
            } else if path.is_dir() {
                let candidate = path.join(NAME_OF_PYPROJECT_FILE);
                if candidate.exists() {
                    paths.insert(candidate);
                }
            } else {
                logging::warning(
                    LOGGER_GLOBS,
                    &format!("Skipping {}: not a file or directory.", path_as_uri(&path)),
                );
            }
        }
    }
    paths
}

/// All `pyproject.toml` files of the project: the root first, then the workspace members (`members` minus
/// `exclude` of `[tool.uv.workspace]`) in path order.
///
/// # Errors
///
/// When the root file is missing, or a file cannot be read or parsed.
pub fn get_all_pyprojects_by_project_root_path(project_root_path: &Path) -> Result<Vec<PyProject>> {
    let root = PyProject::load(get_and_check_path_to_pyproject(project_root_path)?)?;
    let workspace = read_uv_tool_config(&root.doc, &root.path)?.workspace;

    let members = get_pyproject_paths_by_globs(project_root_path, &workspace.members);
    let excluded = get_pyproject_paths_by_globs(project_root_path, &workspace.exclude);

    let mut items = vec![root];
    for path in members.difference(&excluded) {
        items.push(PyProject::load(path.clone())?);
    }
    Ok(items)
}
