import enum

from pydantic import BaseModel, ConfigDict

from uv_upx.services.dependency_up.models.dependencies_list import TomlBasedDependenciesList


class DependencySection(enum.StrEnum):
    MAIN = "project.dependencies"
    DEPENDENCY_GROUPS = "dependency-groups"
    OPTIONAL_DEPENDENCIES = "project.optional-dependencies"


class DependencyGroup(BaseModel):
    section: DependencySection
    dependencies: TomlBasedDependenciesList

    group_name: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
