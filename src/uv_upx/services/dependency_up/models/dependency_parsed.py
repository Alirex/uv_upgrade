from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field

from uv_upx.services.dependency_up.constants.operators import VERSION_OPERATORS_I_ALL
from uv_upx.services.package_name import PackageName

# TODO: (?) Use this?
#   from packaging.specifiers import SpecifierSet
#   from packaging.version import Version


def validate_version_value(value: str) -> str:
    if not value.strip():
        msg = "Version value cannot be empty or whitespace"
        raise ValueError(msg)

    if not value[0].isdigit():
        msg = "Version value must start with a digit"
        raise ValueError(msg)

    return value


def validate_operator(value: str) -> str:
    if value not in VERSION_OPERATORS_I_ALL:
        msg = f"Operator must be one of {VERSION_OPERATORS_I_ALL}"
        raise ValueError(msg)
    return value


class VersionConstraint(BaseModel):
    operator: Annotated[str, AfterValidator(validate_operator)]
    version: Annotated[str, AfterValidator(validate_version_value)]

    def __str__(self) -> str:
        return f"{self.operator}{self.version}"


type DependencyString = str
"""Dependency string from pyproject.toml

Like:
- requests[dev] >=1.2.3; python_version >= "3.10"
- faker>=30.1
"""


class DependencyParsed(BaseModel):
    # https://peps.python.org/pep-0508/

    original_name: str | None = None
    """Original dependency name (e.g., reQuests).

    None if not preserved.
    """

    package_name: PackageName
    """Normalized package name (e.g., requests).

    Needed for better search.
    """

    extras: list[str] = Field(default_factory=list)
    """Extras (e.g., [dev])"""

    version_constraints: list[VersionConstraint] = Field(default_factory=list)
    """Version constraints (e.g., `>=1.2.3`, `==4.5.6`)"""

    marker: str | None = None
    """Environment marker (after ;)"""

    def get_full_spec(
        self,
    ) -> str:
        parts: list[str] = []

        if self.original_name is not None:
            parts.append(self.original_name)
        else:
            parts.append(str(self.package_name))

        if self.extras:
            extras_str = ",".join(self.extras)
            parts.append(f"[{extras_str}]")
        if self.version_constraints:
            vc_strs = [f"{vc!s}" for vc in self.version_constraints]
            parts.append(",".join(vc_strs))
        if self.marker:
            parts.append(f"; {self.marker}")
        return "".join(parts)
