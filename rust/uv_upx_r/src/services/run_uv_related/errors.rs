use thiserror::Error;

#[derive(Error, Debug)]
pub enum RunUvRelatedError {
    #[error("Failed to resolve dependency: {0}")]
    UnresolvedDependency(String),

    #[error("Failed to execute command: {0}")]
    CommandExecutionError(String),

    #[error("Unexpected error: {0}")]
    UnexpectedError(String),

    #[error("Non-empty local segments error: {0}")]
    NonEmptyLocalSegments(String),
}
