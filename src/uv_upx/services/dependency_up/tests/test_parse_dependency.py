import pytest

from uv_upx.services.dependency_up.models.dependency_parsed import DependencyParsed, VersionConstraint
from uv_upx.services.dependency_up.parse_dependency import parse_dependency
from uv_upx.services.package_name import PackageName


@pytest.mark.parametrize(
    ("dependency_string", "expected"),
    [
        (  # Only name
            "foo",
            DependencyParsed(
                package_name=PackageName("foo"),
            ),
        ),
        #
        (  # Simple version constraint
            "foo>=32.0",
            DependencyParsed(
                package_name=PackageName("foo"),
                version_constraints=[
                    VersionConstraint(
                        operator=">=",
                        version="32.0",
                    ),
                ],
            ),
        ),
        (  # Simple version constraint
            "foo<=32.0",
            DependencyParsed(
                package_name=PackageName("foo"),
                version_constraints=[
                    VersionConstraint(
                        operator="<=",
                        version="32.0",
                    ),
                ],
            ),
        ),
        (  # Multiple version constraints
            "foo[bla,xyz]>=32.0,!=33,<34;python_version<'3.11'",
            DependencyParsed(
                package_name=PackageName("foo"),
                version_constraints=[
                    VersionConstraint(
                        operator=">=",
                        version="32.0",
                    ),
                    VersionConstraint(
                        operator="!=",
                        version="33",
                    ),
                    VersionConstraint(
                        operator="<",
                        version="34",
                    ),
                ],
                extras=["bla", "xyz"],
                marker="python_version<'3.11'",
            ),
        ),
        (  # Multiple version constraints
            'foo[bla,xyz] >=32.0, !=33, <34 ;python_version<"3.11"',
            DependencyParsed(
                package_name=PackageName("foo"),
                version_constraints=[
                    VersionConstraint(
                        operator=">=",
                        version="32.0",
                    ),
                    VersionConstraint(
                        operator="!=",
                        version="33",
                    ),
                    VersionConstraint(
                        operator="<",
                        version="34",
                    ),
                ],
                extras=["bla", "xyz"],
                marker='python_version<"3.11"',
            ),
        ),
    ],
)
def test_parse_dependency(
    dependency_string: str,
    expected: DependencyParsed,
) -> None:
    result = parse_dependency(dependency_string)
    assert result == expected
