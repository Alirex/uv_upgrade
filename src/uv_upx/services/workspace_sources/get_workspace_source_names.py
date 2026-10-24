from typing import TYPE_CHECKING, Any, cast

from uv_upx.services.package_name import PackageName

if TYPE_CHECKING:
    from tomlkit import TOMLDocument


def get_workspace_source_names(data: TOMLDocument) -> set[PackageName]:
    """Names of packages that come from the uv workspace.

    They are listed in `[tool.uv.sources]` as `{ workspace = true }`.
    uv always resolves them to the local package, so a version constraint on them is meaningless.

    https://docs.astral.sh/uv/concepts/projects/dependencies/#workspace-member
    """
    sources: dict[str, Any] = cast("dict[str, Any]", data.get("tool", {}).get("uv", {}).get("sources", {}))  # pyright: ignore[reportUnknownMemberType]
    return {
        PackageName(name)
        for name, spec in sources.items()
        if isinstance(spec, dict) and cast("dict[str, Any]", spec).get("workspace") is True
    }
