---
id: D-261128-keep-published-package-name
status: accepted
date: 2026-11-28
reopen_when: a 1.0 release, a breaking API change, or a decision to move the repo to the evocaslab org
---

# Keep the published name `uv-upx` instead of `evocaslab-uv-upx`

## Context

The public-repo standard asks for registry names `evocaslab-<name>`. `uv-upx` has been on PyPI since 2025-12-10 (<https://pypi.org/project/uv-upx/>), and it has 13 releases up to 0.5.0. A rename on PyPI is a new package: the old one stays, and every user has to change a manifest line to keep getting fixes.

## Drivers

- users keep working without a change
- one name per package, no two packages with the same code
- the org naming rule for new packages

## Considered options

| Option                                         | Fits the drivers                          | Cost                                | Hard to undo                               | Evidence                           |
| ---------------------------------------------- | ----------------------------------------- | ----------------------------------- | ------------------------------------------ | ---------------------------------- |
| **keep `uv-upx`** (chosen)                     | users: yes; naming rule: no, an exception | none                                | no                                         | <https://pypi.org/project/uv-upx/> |
| publish `evocaslab-uv-upx`, deprecate `uv-upx` | users must move                           | two packages for a while, a release | yes, a published name cannot be taken back | <https://pypi.org/project/uv-upx/> |

## Decision

In the context of a small published package with existing users, facing the org rule for new names, we chose to keep `uv-upx` over a renamed copy, to achieve no breaking change for users, accepting that the `package-names` check of the public-repo standard reports it until the checker has an exception list.

## Consequences

- Good: no user has to change a manifest; links on the registry keep working.
- Bad: the name does not follow the `evocaslab-` rule; the public-ready check fails on `package-names`.

## Confirmation

Review only: the manifest name is checked by the public-ready check, which reports it.

## Sources

- <https://pypi.org/project/uv-upx/> (read 2026-11-28)
- Public-repo standard, rule 11 (names of public tools and libraries)
