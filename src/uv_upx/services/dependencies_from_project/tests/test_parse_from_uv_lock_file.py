from uv_upx.services.dependencies_from_project.parse_from_uv_lock_file import parse_from_uv_lock_file
from uv_upx.services.package_name import PackageName


def test_parse_from_uv_lock_file() -> None:
    registry = parse_from_uv_lock_file(
        """
version = 1

[[package]]
name = "Typing_Extensions"
version = "4.15.0"

[[package]]
name = "pydantic"
version = "2.12.5"

[[package]]
name = "dynamic-version"
source = { editable = "." }
""",
    )

    assert registry.root == {
        PackageName("typing-extensions"): "4.15.0",
        PackageName("pydantic"): "2.12.5",
    }
