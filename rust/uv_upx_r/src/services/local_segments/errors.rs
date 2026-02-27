use thiserror::Error;
#[derive(Error, Debug)]
pub enum LocalSegmentsError {
    /// Non-empty local segments error.
    ///
    /// Raised when uv have an error like:
    /// - Operator >= is incompatible with versions containing non-empty local segments (`+foo`)
    #[error("Non-empty local segments error: {0}")]
    NonEmptyLocalSegments(String),
}
