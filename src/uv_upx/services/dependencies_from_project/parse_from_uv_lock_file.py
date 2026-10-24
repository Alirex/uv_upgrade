from pydantic import BaseModel, Field

from uv_upx.services.dependencies_from_project.models import DependenciesRegistry, Version
from uv_upx.services.package_name import PackageName
from uv_upx.services.toml import toml_parse


class UvLockPackage(BaseModel):
    """One `[[package]]` entry of `uv.lock`. Only the fields we need."""

    name: PackageName
    version: str | None = None


class UvLockFile(BaseModel):
    """Typed read-only view of `uv.lock`."""

    package: list[UvLockPackage] = Field(default_factory=list)


def parse_from_uv_lock_file(
    content: str,
) -> DependenciesRegistry:
    lock_file = UvLockFile.model_validate(toml_parse(content).unwrap())

    dependencies = DependenciesRegistry()
    for package in lock_file.package:
        if package.version is None:
            # Just in case. Possible problem with "[tool.hatch.version]"
            # https://github.com/zundertj/uv-bump/issues/5
            continue

        dependencies[package.name] = Version(package.version)

    return dependencies
