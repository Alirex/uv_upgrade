from html import escape
from typing import TYPE_CHECKING

from prompt_toolkit import HTML, choice, print_formatted_text

if TYPE_CHECKING:
    import pathlib

    from uv_upx.services.collect_dependencies.models import DependencyGroupParsed
    from uv_upx.services.dependency_up.models.changes_list import ChangesItem


def show_interactive_information() -> None:
    message = """You are running in interactive mode.
You will be prompted for each proposed change.

Note: These changes related to updating dependencies in pyproject.toml files.
It is implying how dependencies will be updated.
But, if you reject ">=X.Y.Z" change, it will not updated in pyproject.toml,
but it may still be updated in the lock file (e.g., uv.lock).
"""
    print(message)


def ask_interactive_confirmation(
    changes_item: ChangesItem,
    group: DependencyGroupParsed,
    path: pathlib.Path,
) -> bool:
    """Ask the user for confirmation in interactive mode."""
    print("=" * 40)
    print(f"In file: {path.as_uri()}")
    folder_name = path.parent.name
    print_formatted_text(HTML(f"Parent folder: <b>{folder_name}</b>"))

    group_title = str(group.section)
    if group.group_name:
        group_title += f"[{group.group_name}]"
    print_formatted_text(HTML(f"Group: <b>{group_title}</b>"))

    message = HTML(
        f"<ansiblue><b>{escape(changes_item.from_item.get_name_with_extras())}:</b></ansiblue> "
        f"<ansired>{escape(changes_item.from_item.get_partial_spec())}</ansired>"
        f" <ansiyellow>&#8594;</ansiyellow> "
        f"<ansigreen>{escape(changes_item.to_item.get_partial_spec())}</ansigreen>",
    )

    result = choice(
        message=message,
        options=[
            (True, "Accept"),
            (False, "Reject"),
        ],
        default=True,
        #
        enable_interrupt=True,
    )

    print("=" * 40)

    return result
