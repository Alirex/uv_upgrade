from typing import TYPE_CHECKING

import tomlkit
from tomlkit import TOMLDocument

if TYPE_CHECKING:
    from pathlib import Path

# TODO: (?) Use also "https://github.com/galactixx/tomlkit-extras"


def toml_parse(content: str) -> TOMLDocument:
    return tomlkit.parse(content)


def toml_load(path: Path) -> TOMLDocument:
    return toml_parse(path.read_text(encoding="utf-8"))


def toml_dumps(data: TOMLDocument) -> str:
    return tomlkit.dumps(data)  # pyright: ignore[reportUnknownMemberType]


def toml_save(path: Path, data: TOMLDocument) -> None:
    text = toml_dumps(data)
    path.write_text(text, encoding="utf-8")
