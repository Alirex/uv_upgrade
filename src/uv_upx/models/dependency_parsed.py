from pydantic import BaseModel

from uv_upx.services.get_deps_from_project import DependencyName


class VersionConstraint(BaseModel):
    operator: str
    version: str


class DependencyParsed(BaseModel):
    # https://peps.python.org/pep-0508/

    dependency_name: DependencyName
    """Dependency name (e.g., requests)"""

    extras: list[str] | None
    """Extras (e.g., [dev])"""

    version_constraints: list[VersionConstraint]
    """Version constraints (e.g., >=1.2.3, ==4.5.6)"""

    marker: str | None
    """Environment marker (after ;)"""

    def get_full_spec(self) -> str:
        parts: list[str] = [self.dependency_name]
        if self.extras:
            extras_str = ",".join(self.extras)
            parts.append(f"[{extras_str}]")
        if self.version_constraints:
            vc_strs = [f"{vc.operator}{vc.version}" for vc in self.version_constraints]
            parts.append(",".join(vc_strs))
        if self.marker:
            parts.append(f"; {self.marker}")
        return "".join(parts)
