import pytest

from uv_upx.services.dependencies_from_project import Version
from uv_upx.services.dependency_up.models.dependency_parsed import VersionConstraint
from uv_upx.services.dependency_up.update_dependency import handle_version_constraint


@pytest.mark.parametrize(
    ("version_constraint", "version_new", "expected"),
    [
        (  # Main case. We focus mainly on this case.
            VersionConstraint(
                operator=">=",
                version="32.0",
            ),
            "33.1",
            ">=33.1",
        ),
        (  # Need to get a previous version if we want to implement an update.
            #   This includes handling alpha/beta/rc versions. So, just skip.
            VersionConstraint(
                operator=">",
                version="32.0",
            ),
            "33.1",
            ">32.0",
        ),
        (  # Not possible by uv. But check just in case.
            VersionConstraint(
                operator="==",
                version="32.0",
            ),
            "33.1",
            "==32.0",
        ),
        (  # Not possible by uv. But check just in case.
            VersionConstraint(
                operator="<",
                version="32.0",
            ),
            "33.1",
            "<32.0",
        ),
    ],
)
def test_handle_version_constraint(
    version_constraint: VersionConstraint,
    version_new: str,
    expected: str,
) -> None:
    handle_version_constraint(
        version_constraint=version_constraint,
        version_new=Version(version_new),
    )
    assert str(version_constraint) == expected
