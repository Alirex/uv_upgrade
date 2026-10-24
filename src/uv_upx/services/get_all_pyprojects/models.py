import pathlib
from typing import ClassVar

from pydantic import BaseModel, ConfigDict
from tomlkit import TOMLDocument

type PathToPyprojectToml = pathlib.Path
"""Path to a pyproject.toml file."""


class PyProjectWrapper(BaseModel):
    path: PathToPyprojectToml
    data: TOMLDocument

    model_config: ClassVar[ConfigDict] = ConfigDict(
        arbitrary_types_allowed=True,
    )


class PyProjectsRegistry(BaseModel):
    items: list[PyProjectWrapper]
