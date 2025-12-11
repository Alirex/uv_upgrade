import pytest

from uv_upx.services.package_name import normalize_package_name


@pytest.mark.parametrize(
    ("package_name", "expected"),
    [
        ("foo", "foo"),
        ("Foo", "foo"),
        ("FoO", "foo"),
        ("FoO-bar", "foo-bar"),
        ("FoO_bar", "foo-bar"),
        #
        ("TOMLKit", "tomlkit"),
        ("Pydantic", "pydantic"),
        ("pyTEST_BenchMark", "pytest-benchmark"),
    ],
)
def test_package_name_normalization(
    package_name: str,
    expected: str,
) -> None:
    result = normalize_package_name(package_name)
    assert result == expected
