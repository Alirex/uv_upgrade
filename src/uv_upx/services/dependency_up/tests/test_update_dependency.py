import pytest

from uv_upx.services.dependencies_from_project import DependenciesRegistry, Version
from uv_upx.services.dependency_up.parse_dependency import parse_dependency
from uv_upx.services.dependency_up.update_dependency import update_dependency_v2
from uv_upx.services.package_name import PackageName
from uv_upx.services.upgrade_profile import UpgradeProfile


@pytest.fixture
def dependencies_registry() -> DependenciesRegistry:
    return DependenciesRegistry(
        {
            PackageName("httpx"): Version("0.28.1"),
            PackageName("pydantic"): Version("2.12.5"),
        },
    )


@pytest.mark.parametrize(
    ("dependency", "profile", "expected"),
    [
        # Lower bound is raised.
        ("httpx>=0.24.0", UpgradeProfile.DEFAULT, "httpx>=0.28.1"),
        # No constraint: a lower bound is added.
        ("httpx", UpgradeProfile.DEFAULT, "httpx>=0.28.1"),
        # Extras and markers are kept.
        (
            'httpx[http2]>=0.24.0; python_version >= "3.14"',
            UpgradeProfile.DEFAULT,
            'httpx[http2]>=0.28.1; python_version >= "3.14"',
        ),
        # Upper bound is kept, lower bound is raised.
        ("httpx>=0.24.0,<1", UpgradeProfile.DEFAULT, "httpx>=0.28.1,<1"),
        # Pinned: changed only with the "with_pinned" profile.
        ("pydantic==2.0.0", UpgradeProfile.DEFAULT, None),
        ("pydantic==2.0.0", UpgradeProfile.WITH_PINNED, "pydantic==2.12.5"),
        # Already up to date.
        ("pydantic>=2.12.5", UpgradeProfile.DEFAULT, None),
    ],
)
def test_update_dependency(
    dependencies_registry: DependenciesRegistry,
    dependency: str,
    profile: UpgradeProfile,
    expected: str | None,
) -> None:
    parsed = parse_dependency(dependency)

    change = update_dependency_v2(
        dependencies_registry=dependencies_registry,
        parsed=parsed,
        profile=profile,
    )

    if expected is None:
        assert change is None
    else:
        assert change is not None
        assert change.from_item.get_full_spec() == parse_dependency(dependency).get_full_spec()
        assert change.to_item.get_full_spec() == expected


def test_update_dependency_not_in_registry(dependencies_registry: DependenciesRegistry) -> None:
    change = update_dependency_v2(
        dependencies_registry=dependencies_registry,
        parsed=parse_dependency("unknown>=1.0"),
        profile=UpgradeProfile.DEFAULT,
    )
    assert change is None
