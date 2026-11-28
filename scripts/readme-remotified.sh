#!/usr/bin/env bash
# Usage: scripts/readme-remotified.sh build|check [file]
#
# build: write README.remotified.md (the PyPI readme) from README.md with every relative link made absolute and
#        pinned to the tag of the version in pyproject.toml (v<version>), so a release's PyPI page links to the files
#        of that release, not to main. The version bump before a release regenerates it.
# check: fail when the file (default README.remotified.md) has a link target that is not http(s), `#` or mailto:
#        (a relative link is broken on PyPI).
set -euo pipefail

repo_url="https://github.com/Alirex/uv_upgrade"
raw_url="https://raw.githubusercontent.com/Alirex/uv_upgrade"

build() {
    local tag
    tag="v$(uv version --short)"
    uv run mdremotifier --input README.md --output README.remotified.md \
        --url-prefix "${repo_url}/blob/${tag}/" --img-url-prefix "${raw_url}/${tag}/"
}

check() {
    local file="${1:-README.remotified.md}"
    local targets bad
    # Inline links and images `](target)`, and reference definitions `[name]: target`.
    targets="$(
        {
            grep -oE '\]\([^) ]+' "${file}" | sed -E 's/^\]\(//' || true
            grep -oE '^\[[^]]+\]: *[^ ]+' "${file}" | sed -E 's/^\[[^]]+\]: *//' || true
        }
    )"
    bad="$(printf '%s\n' "${targets}" | grep -vE '^(https?://|#|mailto:|$)' || true)"
    if [[ -n "${bad}" ]]; then
        echo "${file}: link targets that do not open on PyPI:" >&2
        printf '  %s\n' "${bad}" >&2
        exit 1
    fi
    echo "OK: ${file} links are absolute"
}

case "${1:-}" in
build) build ;;
check) check "${2:-}" ;;
*)
    sed -n '2,9p' "$0" >&2
    exit 2
    ;;
esac
