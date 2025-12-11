from typing import NewType

from pydantic import Field, RootModel

from uv_upx.services.package_name import PackageName

Version = NewType("Version", str)

type DependenciesRegistryInternal = dict[PackageName, Version]


class DependenciesRegistry(RootModel[DependenciesRegistryInternal]):
    """Registry of dependencies with their versions.

    Source of truth for the dependencies.
    """

    root: DependenciesRegistryInternal = Field(default_factory=dict)

    def __getitem__(self, item: PackageName) -> Version:
        return self.root[item]

    def __setitem__(self, key: PackageName, value: Version) -> None:
        self.root[key] = value
