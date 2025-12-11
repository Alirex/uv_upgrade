from uv_upx.services.dependency_up import IncludedDependencyGroup

type TomlBasedDependenciesList = list[str] | list[str | IncludedDependencyGroup]
"""List of dependencies from TOML document

Data needed to be changed directly in this list to preserve comments.
"""
