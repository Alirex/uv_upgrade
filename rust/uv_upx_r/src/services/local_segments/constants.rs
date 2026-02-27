pub const ERROR_TEXT_PART_I_NON_EMPTY_LOCAL_SEGMENT: &str =
    "Operator >= is incompatible with versions containing non-empty local segments";

/// Indicates the presence of a local segment in a version specifier.
///
/// For example, in the version "1.0.0+foo", the "+foo" part is the local segment.
pub const LOCAL_SEGMENT_CHAR_INDICATOR: &str = "+";
