from uv_upx.services.dependencies_from_project.models import DependenciesRegistry, Version
from uv_upx.services.package_name import PackageName
from uv_upx.services.toml import toml_parse


def parse_from_uv_lock_file(
    content: str,
) -> DependenciesRegistry:
    data = toml_parse(content)

    dependencies = DependenciesRegistry()
    for package in data.get("package", []):  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        version = package.get("version")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

        if version is None:
            # Just in case. Possible problem with "[tool.hatch.version]"
            # https://github.com/zundertj/uv-bump/issues/5
            continue

        dependencies[PackageName(package["name"])] = Version(version)  # pyright: ignore[reportUnknownArgumentType] # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]

    return dependencies
