import pathlib

from pydantic import BaseModel, ConfigDict
from tomlkit import TOMLDocument

type PathToPyprojectToml = pathlib.Path
"""Path to a pyproject.toml file."""


class PyProjectWrapper(BaseModel):
    path: PathToPyprojectToml
    data: TOMLDocument

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class PyProjectsRegistry(BaseModel):
    items: list[PyProjectWrapper]
