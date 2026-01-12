from typing import Final

ERROR_TEXT_PART_I_NON_EMPTY_LOCAL_SEGMENT: Final[str] = (
    "Operator >= is incompatible with versions containing non-empty local segments"
)

LOCAL_SEGMENT_CHAR_INDICATOR: Final[str] = "+"
"""Indicates the presence of a local segment in a version specifier.

For example, in the version "1.0.0+foo", the "+foo" part is the local segment.
"""
