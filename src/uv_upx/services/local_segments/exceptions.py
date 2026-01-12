class NonEmptyLocalSegmentsError(Exception):
    """Non-empty local segments error.

    Raised when uv have an error like:

    `Operator >= is incompatible with versions containing non-empty local segments (`+foo`)

    """
