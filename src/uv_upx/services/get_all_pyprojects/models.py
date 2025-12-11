import pathlib

from pydantic import BaseModel, ConfigDict
from tomlkit import TOMLDocument


class PyProjectWrapper(BaseModel):
    path: pathlib.Path
    data: TOMLDocument

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class PyProjectsRegistry(BaseModel):
    items: list[PyProjectWrapper]
