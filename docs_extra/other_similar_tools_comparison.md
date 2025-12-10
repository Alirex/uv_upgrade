# Other similar tools comparison

Legend

- ✅ supported
- ❌ not supported
- ⚠️ partially supported. Or have some limitations.
- ❔ unknown

| Name                                               | Description                                                                                                                                                                              | Lang   | Latest info                          | Comments preserved | Workspace support | Preserve pinned versions | Update >= constraints | Respect ranges constraints |
| -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------ | ------------------ | ----------------- | ------------------------ | --------------------- | -------------------------- |
| [uv-upx](https://pypi.org/project/uv-upx/)         | Upgrade dependencies in `pyproject.toml` files with `uv`. <br/> <br/> Update lock file by uv. Write changes by tomlkit.                                                                  | Python | 2025.12.10<br/>0.2.0                 | ✅️                 | ✅                | ✅                       | ✅                    | ✅                         |
| [uv-bump](https://pypi.org/project/uv-bump/)       | Bump pyproject.toml dependency minimum versions to latest feasible versions. <br/> <br/> Update lock file by uv. Update pyproject.toml by regex. So, false-positive changes can be done. | Python | 2025.12.07<br/>0.3.2                 | ⚠️                 | ❌                | ✅                       | ✅                    | ❔                         |
| [uv-upgrade](https://pypi.org/project/uv-upgrade/) | - <br/><br/> The update is done by reinstalling the dependency (remove/add)                                                                                                              | Python | 2025.03.17<br/>0.2.1.2<br/>(no repo) | ❌                 | ❌                | ❌                       | ✅                    | ❌                         |
| [uv-up](https://pypi.org/project/uv-up/)           | Not implemented                                                                                                                                                                          | Python | 2024.10.26<br/>0.1.0                 | ❌                 | ❌                | ❌                       | ❌                    | ❌                         |
