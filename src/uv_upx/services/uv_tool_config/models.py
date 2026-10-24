from typing import Annotated, ClassVar, TypeIs

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


def _is_table(value: object) -> TypeIs[dict[str, object]]:
    return isinstance(value, dict)


def _keep_only_tables(value: object) -> object:
    """Replace everything that is not a table with `None`.

    A source can be a table or a list of tables (with markers). Only a plain table can be `{ workspace = true }`.
    """
    return value if _is_table(value) else None


class UvSourceSpec(BaseModel):
    """One entry of `[tool.uv.sources]`. Only the fields we need."""

    workspace: object = None

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    @property
    def is_workspace(self) -> bool:
        return self.workspace is True


class UvWorkspaceConfig(BaseModel):
    """`[tool.uv.workspace]`.

    https://docs.astral.sh/uv/concepts/projects/workspaces/
    """

    members: list[str] = Field(default_factory=list)
    exclude: list[str] = Field(default_factory=list)


class UvToolConfig(BaseModel):
    """`[tool.uv]`. Only the fields we need."""

    workspace: UvWorkspaceConfig = Field(default_factory=UvWorkspaceConfig)
    sources: dict[str, Annotated[UvSourceSpec | None, BeforeValidator(_keep_only_tables)]] = Field(
        default_factory=dict,
    )


class ToolTable(BaseModel):
    """`[tool]`."""

    uv: UvToolConfig = Field(default_factory=UvToolConfig)


class PyProjectUvView(BaseModel):
    """Typed read-only view of the uv-related parts of a `pyproject.toml`."""

    tool: ToolTable = Field(default_factory=ToolTable)
