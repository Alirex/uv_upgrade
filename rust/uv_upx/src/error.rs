//! The error type of the library. Messages copy the Python exceptions where the user sees them.

use std::path::PathBuf;

/// Everything that can go wrong in the library.
#[derive(Debug, thiserror::Error)]
pub enum Error {
    /// `--project` does not point to a directory (`NotADirectoryError` in Python).
    #[error("Path {} is not a directory.", .0.display())]
    NotADirectory(PathBuf),

    /// A required file is missing (`FileNotFoundError` in Python).
    #[error("Path {} does not exist.", .0.display())]
    NotFound(PathBuf),

    /// Reading or writing a file failed.
    #[error("{action} {}: {source}", path.display())]
    Io {
        /// What was attempted, like "Failed to read".
        action: &'static str,
        /// The file.
        path: PathBuf,
        /// The OS error.
        #[source]
        source: std::io::Error,
    },

    /// Running `uv` failed before it produced an exit code (not installed, not executable).
    #[error("Failed to run 'uv': {0}")]
    UvNotRunnable(#[source] std::io::Error),

    /// A TOML file does not parse.
    #[error("Invalid TOML in {}: {source}", path.display())]
    Toml {
        /// The file.
        path: PathBuf,
        /// The parser error.
        #[source]
        source: toml_edit::TomlError,
    },

    /// A value in `pyproject.toml` or `uv.lock` has the wrong shape (pydantic `ValidationError` in Python).
    #[error("Invalid value in {}: {detail}", path.display())]
    Validation {
        /// The file.
        path: PathBuf,
        /// What is wrong.
        detail: String,
    },

    /// A dependency string does not parse (`ValueError` in Python).
    #[error("{0}")]
    InvalidDependency(String),

    /// `uv lock` failed.
    #[error("Failed to resolve dependencies with 'uv lock'. Please check your dependency specifications.")]
    UnresolvedLock,

    /// `uv lock` failed because of `>=` constraints on versions with local segments.
    #[error(
        "Failed to resolve dependencies with 'uv lock' due to non-empty local segments. \
         Please check your dependency specifications."
    )]
    NonEmptyLocalSegments,

    /// `uv sync` failed.
    #[error("Failed to sync dependencies with 'uv sync'. Please check your dependency specifications.")]
    UnresolvedSync,

    /// The interactive prompt failed or was interrupted.
    #[error("Interactive prompt failed: {0}")]
    Prompt(String),
}

impl Error {
    /// The text Python's `type(e)` gives for the matching exception (used in one log message of the updater).
    #[must_use]
    pub fn python_type(&self) -> &'static str {
        match self {
            Self::NotADirectory(_) => "<class 'NotADirectoryError'>",
            Self::NotFound(_) => "<class 'FileNotFoundError'>",
            Self::Io { .. } | Self::UvNotRunnable(_) => "<class 'OSError'>",
            Self::Toml { .. } => "<class 'tomlkit.exceptions.ParseError'>",
            Self::Validation { .. } => "<class 'pydantic_core._pydantic_core.ValidationError'>",
            Self::InvalidDependency(_) => "<class 'ValueError'>",
            Self::UnresolvedLock | Self::UnresolvedSync => {
                "<class 'uv_upx.services.run_uv_related.exceptions.UnresolvedDependencyError'>"
            }
            Self::NonEmptyLocalSegments => {
                "<class 'uv_upx.services.local_segments.exceptions.NonEmptyLocalSegmentsError'>"
            }
            Self::Prompt(_) => "<class 'KeyboardInterrupt'>",
        }
    }
}

/// The result type of the library.
pub type Result<T> = std::result::Result<T, Error>;

/// Read a file as UTF-8 text with the path in the error.
///
/// # Errors
///
/// `Error::Io` when the file cannot be read.
pub fn read_text(path: &std::path::Path) -> Result<String> {
    std::fs::read_to_string(path).map_err(|source| Error::Io {
        action: "Failed to read",
        path: path.to_path_buf(),
        source,
    })
}

/// Write a text file with the path in the error.
///
/// # Errors
///
/// `Error::Io` when the file cannot be written.
pub fn write_text(path: &std::path::Path, text: &str) -> Result<()> {
    std::fs::write(path, text).map_err(|source| Error::Io {
        action: "Failed to write",
        path: path.to_path_buf(),
        source,
    })
}
