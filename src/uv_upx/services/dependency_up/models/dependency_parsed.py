from pydantic import BaseModel

from uv_upx.services.package_name import PackageName


class VersionConstraint(BaseModel):
    operator: str
    version: str


class DependencyParsed(BaseModel):
    # https://peps.python.org/pep-0508/

    original_name: str | None = None
    """Original dependency name (e.g., reQuests).

    None if not preserved.
    """

    dependency_name: PackageName
    """Normalized dependency name (e.g., requests).

    Needed for better search.
    """

    extras: list[str] | None
    """Extras (e.g., [dev])"""

    version_constraints: list[VersionConstraint]
    """Version constraints (e.g., `>=1.2.3`, `==4.5.6`)"""

    marker: str | None
    """Environment marker (after ;)"""

    def get_full_spec(
        self,
    ) -> str:
        parts: list[str] = []

        if self.original_name is not None:
            parts.append(self.original_name)
        else:
            parts.append(str(self.dependency_name))

        if self.extras:
            extras_str = ",".join(self.extras)
            parts.append(f"[{extras_str}]")
        if self.version_constraints:
            vc_strs = [f"{vc.operator}{vc.version}" for vc in self.version_constraints]
            parts.append(",".join(vc_strs))
        if self.marker:
            parts.append(f"; {self.marker}")
        return "".join(parts)
