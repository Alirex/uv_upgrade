use crate::services::toml::TomlDocumentMut;
use std::path::PathBuf;

/// Path to a pyproject.toml file.
pub type PathToPyprojectToml = PathBuf;

#[derive(Debug, Clone)]
pub struct PyProjectWrapper {
    pub path: PathToPyprojectToml,
    pub data: TomlDocumentMut,
}
