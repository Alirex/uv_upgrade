import re
from re import Pattern
from typing import Final

from uv_upx.services.dependency_up.constants.operators import VERSION_OPERATORS_I_ALL
from uv_upx.services.dependency_up.models.dependency_parsed import DependencyParsed, DependencyString, VersionConstraint
from uv_upx.services.package_name import PackageName

VERSION_OPERATORS_AS_OR: Final[str] = "|".join(sorted(VERSION_OPERATORS_I_ALL, key=lambda x: len(x), reverse=True))

# https://peps.python.org/pep-0440/#version-specifiers
PATTERN_I_DEPENDENCY_STRING: Final[Pattern[str]] = re.compile(
    rf"""^
\s*
(?P<name>[A-Za-z0-9_.+-]+)                       # package name (letters, digits, _ . + -)
\s*
(?:\[(?P<extras>[^\]]+)\])?                       # optional extras inside [...]
\s*
(?P<version_constraints>                           # optional version constraints (comma separated)
    (?:
        (?:(?:{VERSION_OPERATORS_AS_OR})\s*[^,;\[]+)    # single constraint starting with an operator
        (?:\s*,\s*(?:(?:{VERSION_OPERATORS_AS_OR})\s*[^,;\[]+))*  # optional additional constraints
    )
)?
\s*
(?:;\s*(?P<marker>.*))?                           # optional environment marker after ';'
$
""",
    re.IGNORECASE | re.VERBOSE,
)

PATTERN_I_VERSION_CONSTRAINT: Final[Pattern[str]] = re.compile(
    rf"""^
\s*
(?P<operator>{VERSION_OPERATORS_AS_OR})          # version operator
\s*
(?P<version>[^{VERSION_OPERATORS_AS_OR}]+)                # version value
\s*$
""",
    re.IGNORECASE | re.VERBOSE,
)


def parse_dependency(
    dependency_string: DependencyString,
    #
    *,
    preserve_original_package_names: bool = False,
) -> DependencyParsed:  # sourcery skip: low-code-quality
    dependency_string = dependency_string.strip()

    match = PATTERN_I_DEPENDENCY_STRING.match(dependency_string)

    if not match:
        msg = f"Invalid dependency string: {dependency_string}"
        raise ValueError(msg)

    name = match.group("name")

    extras_raw = match.group("extras") or ""
    extras = [item_ for item in extras_raw.split(",") if (item_ := item.strip())]

    version_constraints_raw = match.group("version_constraints") or ""
    version_constraints = parse_version_constraints(version_constraints_raw)

    marker_raw = match.group("marker")
    marker = marker_raw.strip() if marker_raw else None

    return DependencyParsed(
        original_name=name if preserve_original_package_names else None,
        package_name=PackageName(name),
        extras=extras,
        version_constraints=version_constraints,
        marker=marker,
    )


def parse_version_constraints(
    version_part: str,
) -> list[VersionConstraint]:
    # parse version constraints (comma separated)
    version_constraints: list[VersionConstraint] = []

    if not version_part:
        return version_constraints

    # do not attempt to parse direct URL / VCS refs (start with '@')
    if version_part.startswith("@"):
        msg = f"Invalid version_part string: '{version_part}'"
        raise ValueError(msg)

    raw_parts = [p.strip() for p in version_part.split(",") if p.strip()]

    for raw_part in raw_parts:
        match_vc = PATTERN_I_VERSION_CONSTRAINT.match(raw_part.strip())
        if not match_vc:
            msg = f"Invalid version constraint: '{raw_part}'"
            raise ValueError(msg)

        operator = match_vc.group("operator")
        version = match_vc.group("version")

        if operator not in VERSION_OPERATORS_I_ALL:
            msg = f"Invalid version operator: '{operator}'"
            raise ValueError(msg)

        version_constraint = VersionConstraint(
            operator=operator,
            version=version,
        )
        version_constraints.append(version_constraint)

    return version_constraints
