import re
from re import Pattern
from typing import Annotated, Final

from pydantic import AfterValidator, ConfigDict, RootModel

PATTERN_I_NORMALIZED_I_TO_REPLACE: Final[Pattern[str]] = re.compile(r"[-_.]+")
CHAR_I_TO_USE: Final[str] = "-"


def normalize_package_name(package_name: str) -> str:
    """Normalize the package name according to PEP 503.

    https://peps.python.org/pep-0503/

    https://packaging.python.org/en/latest/specifications/name-normalization/
    """
    return PATTERN_I_NORMALIZED_I_TO_REPLACE.sub(CHAR_I_TO_USE, package_name).lower()


class PackageName(RootModel[str]):
    root: Annotated[str, AfterValidator(normalize_package_name)]

    def __str__(self) -> str:
        return self.root

    model_config = ConfigDict(
        frozen=True,
    )
