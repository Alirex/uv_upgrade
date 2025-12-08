from typing import TYPE_CHECKING

import tomlkit
from tomlkit import TOMLDocument

if TYPE_CHECKING:
    from pathlib import Path

# TODO: (?) Use also "https://github.com/galactixx/tomlkit-extras"


def load_toml(path: Path) -> TOMLDocument:
    return tomlkit.parse(path.read_text(encoding="utf-8"))


def save_toml(path: Path, data: TOMLDocument) -> None:
    text = tomlkit.dumps(data)  # pyright: ignore[reportUnknownMemberType]
    path.write_text(text, encoding="utf-8")
