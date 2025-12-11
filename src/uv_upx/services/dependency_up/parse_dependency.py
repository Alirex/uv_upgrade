from uv_upx.services.dependency_up.constants.operators import VERSION_OPERATORS_I_ALL
from uv_upx.services.dependency_up.models.dependency_parsed import DependencyParsed, VersionConstraint
from uv_upx.services.package_name import PackageName


def parse_dependency(  # noqa: C901, PLR0912, PLR0915
    dependency_string: str,
    #
    *,
    preserve_original_package_names: bool = False,
) -> DependencyParsed:  # sourcery skip: low-code-quality
    dependency_string = dependency_string.strip()
    if not dependency_string:
        msg = "Empty dependency string"
        raise ValueError(msg)

    # split off environment marker (after ';')
    parts = dependency_string.split(";", 1)
    main = parts[0].strip()
    marker = parts[1].strip() if len(parts) > 1 else None

    # parse name and extras
    name = main
    extras: list[str] | None = None
    version_part = ""

    if "[" in main:
        i = main.find("[")
        j = main.find("]", i)
        if j == -1:
            msg = f"Invalid dependency string: {main}"
            raise ValueError(msg)
        name = main[:i].strip()
        extras_str = main[i + 1 : j].strip()
        extras = [e.strip() for e in extras_str.split(",") if e.strip()] or None
        version_part = main[j + 1 :].strip()
    else:
        # try to locate the start of version/operator tokens
        ops = VERSION_OPERATORS_I_ALL
        first_pos = None
        for op in ops:
            idx = main.find(op)
            if idx != -1 and (first_pos is None or idx < first_pos):
                first_pos = idx
        if first_pos is not None:
            name = main[:first_pos].strip()
            version_part = main[first_pos:].strip()
        else:
            name = main.strip()
            version_part = ""

    if not name:
        msg = f"Invalid dependency string: {main}"
        raise ValueError(msg)

    # parse version constraints (comma separated)
    version_constraints: list[VersionConstraint] = []
    if version_part:
        # do not attempt to parse direct URL / VCS refs (start with '@')
        if version_part.startswith("@"):
            msg = f"Invalid dependency string: {main}"
            raise ValueError(msg)

        raw_parts = [p.strip() for p in version_part.split(",") if p.strip()]
        op_candidates = VERSION_OPERATORS_I_ALL
        for rp in raw_parts:
            token = rp.lstrip()
            matched = False
            for op in op_candidates:
                if token.startswith(op):
                    ver = token[len(op) :].strip().strip("\"'")
                    version_constraints.append(VersionConstraint(operator=op, version=ver))
                    matched = True
                    break
            if not matched:
                # allow a bit of tolerance for leading space before the operator
                stripped = token.lstrip()
                for op in op_candidates:
                    if stripped.startswith(op):
                        ver = stripped[len(op) :].strip().strip("\"'")
                        version_constraints.append(VersionConstraint(operator=op, version=ver))
                        matched = True
                        break
            if not matched:
                msg = f"Invalid dependency string: {main}"
                raise ValueError(msg)

    return DependencyParsed(
        original_name=name if preserve_original_package_names else None,
        dependency_name=PackageName(name),
        extras=extras,
        version_constraints=version_constraints,
        marker=marker,
    )
