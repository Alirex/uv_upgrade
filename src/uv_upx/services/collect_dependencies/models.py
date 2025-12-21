import enum

from pydantic import BaseModel, ConfigDict

from uv_upx.services.dependency_up.models.dependencies_list import TomlBasedDependenciesList
from uv_upx.services.dependency_up.models.dependency_parsed import DependencyParsed


class DependencySection(enum.StrEnum):
    MAIN = "project.dependencies"
    DEPENDENCY_GROUPS = "dependency-groups"
    OPTIONAL_DEPENDENCIES = "project.optional-dependencies"


type GroupNameOrNone = str | None


class DependencyGroup(BaseModel):
    section: DependencySection
    dependencies: TomlBasedDependenciesList

    group_name: GroupNameOrNone = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class DependencyItemParsed(BaseModel):
    parsed: DependencyParsed
    index_in_group: int


class DependencyGroupParsed(DependencyGroup):
    parsed_dependencies: list[DependencyItemParsed]
