from typing import TYPE_CHECKING

from tomlkit.container import Container, OutOfOrderTableProxy
from tomlkit.items import AbstractTable, Array

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

type TomlTable = Container | AbstractTable | OutOfOrderTableProxy
"""Any tomlkit mapping node. A table that is split in several places of a file becomes `OutOfOrderTableProxy`."""

# Note: tomlkit annotates `OutOfOrderTableProxy.__getitem__` with `Any`.
# Re-binding it with the `object` return type keeps `Any` out of the typed code.
_proxy_get_item: Callable[[OutOfOrderTableProxy, str], object] = OutOfOrderTableProxy.__getitem__


def is_table(node: object) -> bool:
    """Check that the node is a TOML table (also an out-of-order one)."""
    return isinstance(node, Container | AbstractTable | OutOfOrderTableProxy)


def get_node(data: TomlTable, *path: str) -> object:
    """Walk down the tables of a TOML document by keys.

    Return the live tomlkit node (not a copy), so it can be changed in place and written back with its formatting.
    Return `None`, if some key on the way is missing or the parent is not a table.
    """
    node: object = data
    for key in path:
        if (isinstance(node, Container) and key in node) or (isinstance(node, AbstractTable) and key in node):
            node = node[key]
        elif isinstance(node, OutOfOrderTableProxy) and key in node:
            node = _proxy_get_item(node, key)
        else:
            return None
    return node


def get_arrays_in_table(data: TomlTable, *path: str) -> dict[str, Array]:
    """Get the live arrays that are direct values of the table at the path. Other values are skipped."""
    table = get_node(data, *path)
    if not isinstance(table, Container | AbstractTable | OutOfOrderTableProxy):
        return {}
    arrays: dict[str, Array] = {}
    for key in table:
        value = get_node(table, key)
        if isinstance(value, Array):
            arrays[key] = value
    return arrays


def array_items(array: Sequence[object]) -> list[object]:
    """Items of a TOML array (or a list) with the typed `object` elements, in the original order."""
    return list[object](array)
