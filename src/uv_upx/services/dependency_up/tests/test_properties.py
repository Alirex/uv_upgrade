"""Property-based tests: version parsing and the rewrite of one dependency string.

Done-when lines (TDD practice) mapped to tests:

- parsing never loses a part of a dependency string: `test_parse_round_trip`
- a parsed string renders to one stable form: `test_render_is_stable`
- the lower bound ends at the locked version, the other operators stay: `test_update_only_touches_lower_bounds`
- a second upgrade changes nothing: `test_update_is_idempotent`
- names are normalized the same way each time: `test_normalize_package_name_is_idempotent`
"""

from hypothesis import given
from hypothesis import strategies as st

from uv_upx.services.dependencies_from_project import DependenciesRegistry, Version
from uv_upx.services.dependency_up.models.update_options import DependencyUpdateOptions
from uv_upx.services.dependency_up.parse_dependency import parse_dependency
from uv_upx.services.dependency_up.update_dependency import update_dependency_v2
from uv_upx.services.package_name import PackageName, normalize_package_name
from uv_upx.services.upgrade_profile import UpgradeProfile

OPERATORS = [">=", "==", "<", "<=", "~=", ">", "!=", "==="]

names = st.from_regex(r"[A-Za-z][A-Za-z0-9]{0,7}([-_.][A-Za-z0-9]{1,5}){0,2}", fullmatch=True)
extras = st.lists(st.from_regex(r"[a-z][a-z0-9]{0,5}", fullmatch=True), max_size=3, unique=True)
versions = st.from_regex(r"[0-9]{1,3}(\.[0-9]{1,3}){0,3}", fullmatch=True)
constraints = st.lists(st.tuples(st.sampled_from(OPERATORS), versions), max_size=3)
markers = st.one_of(st.none(), st.sampled_from(['python_version >= "3.10"', "sys_platform == 'linux'"]))
profiles = st.sampled_from(list(UpgradeProfile))


def _render(name: str, extra: list[str], constraint: list[tuple[str, str]], marker: str | None) -> str:
    extras_part = f"[{','.join(extra)}]" if extra else ""
    spec = ",".join(f"{op}{ver}" for op, ver in constraint)
    marker_part = f"; {marker}" if marker else ""
    return f"{name}{extras_part}{spec}{marker_part}"


@given(names, extras, constraints, markers)
def test_parse_round_trip(
    name: str,
    extra: list[str],
    constraint: list[tuple[str, str]],
    marker: str | None,
) -> None:
    parsed = parse_dependency(_render(name, extra, constraint, marker))

    assert parsed.package_name == PackageName(name)
    assert parsed.extras == extra
    assert [(vc.operator, vc.version) for vc in parsed.version_constraints] == constraint
    assert parsed.marker == marker


@given(names, extras, constraints, markers)
def test_render_is_stable(
    name: str,
    extra: list[str],
    constraint: list[tuple[str, str]],
    marker: str | None,
) -> None:
    parsed = parse_dependency(_render(name, extra, constraint, marker), preserve_original_package_names=True)

    rendered = parsed.get_full_spec()

    assert rendered.startswith(name)
    again = parse_dependency(rendered, preserve_original_package_names=True)
    assert again == parsed
    assert again.get_full_spec() == rendered


@given(names, extras, constraints, markers, versions, profiles)
def test_update_only_touches_lower_bounds(  # noqa: PLR0913, PLR0917
    name: str,
    extra: list[str],
    constraint: list[tuple[str, str]],
    marker: str | None,
    locked: str,
    profile: UpgradeProfile,
) -> None:
    registry = DependenciesRegistry({PackageName(name): Version(locked)})
    parsed = parse_dependency(_render(name, extra, constraint, marker))

    _ = update_dependency_v2(
        dependencies_registry=registry,
        parsed=parsed,
        options=DependencyUpdateOptions(profile=profile),
    )

    changeable = {">=", "=="} if profile is UpgradeProfile.WITH_PINNED else {">="}
    expected = [(op, locked if op in changeable else ver) for op, ver in constraint] or [(">=", locked)]
    assert [(vc.operator, vc.version) for vc in parsed.version_constraints] == expected
    assert parsed.extras == extra
    assert parsed.marker == marker


@given(names, extras, constraints, markers, versions, profiles)
def test_update_is_idempotent(  # noqa: PLR0913, PLR0917
    name: str,
    extra: list[str],
    constraint: list[tuple[str, str]],
    marker: str | None,
    locked: str,
    profile: UpgradeProfile,
) -> None:
    registry = DependenciesRegistry({PackageName(name): Version(locked)})
    parsed = parse_dependency(_render(name, extra, constraint, marker))
    options = DependencyUpdateOptions(profile=profile)
    _ = update_dependency_v2(dependencies_registry=registry, parsed=parsed, options=options)

    again = parse_dependency(parsed.get_full_spec())

    assert update_dependency_v2(dependencies_registry=registry, parsed=again, options=options) is None


@given(st.from_regex(r"[A-Za-z0-9][A-Za-z0-9._-]{0,15}", fullmatch=True))
def test_normalize_package_name_is_idempotent(name: str) -> None:
    once = normalize_package_name(name)

    assert normalize_package_name(once) == once
    assert once == once.lower()
    assert "_" not in once
    assert "." not in once
