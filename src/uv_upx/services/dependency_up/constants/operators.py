from typing import Final

# https://peps.python.org/pep-0440/#version-specifiers

VERSION_OPERATOR_I_GREATER_OR_EQUAL: Final[str] = ">="
VERSION_OPERATORS_I_PUT_IF_DIFFERENT: Final[set[str]] = {VERSION_OPERATOR_I_GREATER_OR_EQUAL}
VERSION_OPERATORS_I_EXPLICIT_IGNORE: Final[set[str]] = {
    # Pinned versions
    "==",
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

VERSION_OPERATORS_I_ALL: Final[set[str]] = VERSION_OPERATORS_I_PUT_IF_DIFFERENT | VERSION_OPERATORS_I_EXPLICIT_IGNORE
