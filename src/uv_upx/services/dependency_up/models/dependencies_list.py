from tomlkit.items import Array

from uv_upx.services.dependency_up import IncludedDependencyGroup
from uv_upx.services.dependency_up.models.dependency_parsed import DependencyString

type TomlBasedDependenciesList = Array | list[DependencyString] | list[DependencyString | IncludedDependencyGroup]
"""List of dependencies from TOML document

Data needed to be changed directly in this list to preserve comments.
"""
