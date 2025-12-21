from typing import Final

# https://peps.python.org/pep-0440/#version-specifiers

type VERSION_OPERATOR = str

VERSION_OPERATOR_I_GREATER_OR_EQUAL: Final[VERSION_OPERATOR] = ">="

VERSION_OPERATOR_I_EQUAL: Final[VERSION_OPERATOR] = "=="

VERSION_OPERATORS_I_PUT_IF_DIFFERENT: Final[set[VERSION_OPERATOR]] = {
    VERSION_OPERATOR_I_GREATER_OR_EQUAL,
}

VERSION_OPERATORS_I_PINNED_ALLOWED_TO_CHANGE: Final[set[VERSION_OPERATOR]] = {
    VERSION_OPERATOR_I_EQUAL,
}

VERSION_OPERATORS_I_EXPLICIT_IGNORE: Final[set[VERSION_OPERATOR]] = {
    # Pinned versions
    VERSION_OPERATOR_I_EQUAL,
    "===",
    #
    # Upper bounds
    "<",
    "<=",
    #
    # May needed advanced logic here
    "~=",
    #
    # Need to calculate a previous version. Skip for now.
    ">",
    #
    # Special case
    "!=",
}

VERSION_OPERATORS_I_ALL: Final[set[VERSION_OPERATOR]] = (
    VERSION_OPERATORS_I_PUT_IF_DIFFERENT | VERSION_OPERATORS_I_EXPLICIT_IGNORE
)
