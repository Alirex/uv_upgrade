//! The `[tool.uv]` parts of a `pyproject.toml` that the tool reads: the workspace and the workspace sources.

use std::collections::BTreeSet;
use std::path::Path;

use toml_edit::{DocumentMut, Item};

use crate::error::{Error, Result};
use crate::package_name::PackageName;
use crate::toml_access::get_node;

/// `[tool.uv.workspace]` (<https://docs.astral.sh/uv/concepts/projects/workspaces/>).
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct UvWorkspaceConfig {
    /// Member patterns.
    pub members: Vec<String>,
    /// Excluded patterns.
    pub exclude: Vec<String>,
}

/// `[tool.uv]`, only the fields we need.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct UvToolConfig {
    /// The workspace.
    pub workspace: UvWorkspaceConfig,
    /// Sources: name to "is a workspace member" (`{ workspace = true }`). Only plain tables count; a list of
    /// sources (with markers) is never a workspace source.
    pub sources: Vec<(String, bool)>,
}

impl UvToolConfig {
    /// Names of the packages that come from the uv workspace: uv resolves them to the local package, so a version
    /// constraint on them is meaningless and they are skipped.
    #[must_use]
    pub fn workspace_source_names(&self) -> BTreeSet<PackageName> {
        self.sources
            .iter()
            .filter(|(_, is_workspace)| *is_workspace)
            .map(|(name, _)| PackageName::new(name))
            .collect()
    }
}

fn string_list(doc: &DocumentMut, path: &[&str], file: &Path) -> Result<Vec<String>> {
    let Some(item) = get_node(doc, path) else {
        return Ok(Vec::new());
    };
    let array = item.as_array().ok_or_else(|| Error::Validation {
        path: file.to_path_buf(),
        detail: format!("{} must be a list of strings", path.join(".")),
    })?;
    array
        .iter()
        .map(|value| {
            value.as_str().map(ToOwned::to_owned).ok_or_else(|| Error::Validation {
                path: file.to_path_buf(),
                detail: format!("{} must be a list of strings", path.join(".")),
            })
        })
        .collect()
}

/// Read `[tool.uv]` as typed data. `file` names the file in errors.
///
/// # Errors
///
/// `Error::Validation` when `members` or `exclude` is not a list of strings.
pub fn read_uv_tool_config(doc: &DocumentMut, file: &Path) -> Result<UvToolConfig> {
    let workspace = UvWorkspaceConfig {
        members: string_list(doc, &["tool", "uv", "workspace", "members"], file)?,
        exclude: string_list(doc, &["tool", "uv", "workspace", "exclude"], file)?,
    };
    let sources = get_node(doc, &["tool", "uv", "sources"])
        .and_then(Item::as_table_like)
        .map(|table| {
            table
                .iter()
                .map(|(name, spec)| {
                    let is_workspace = spec
                        .as_table_like()
                        .and_then(|spec| spec.get("workspace"))
                        .and_then(Item::as_bool)
                        .is_some_and(|workspace| workspace);
                    (name.to_owned(), is_workspace)
                })
                .collect()
        })
        .unwrap_or_default();
    Ok(UvToolConfig { workspace, sources })
}

/// Names of packages that come from the uv workspace (`{ workspace = true }` in `[tool.uv.sources]`).
///
/// # Errors
///
/// See [`read_uv_tool_config`].
pub fn get_workspace_source_names(doc: &DocumentMut, file: &Path) -> Result<BTreeSet<PackageName>> {
    Ok(read_uv_tool_config(doc, file)?.workspace_source_names())
}

#[cfg(test)]
mod tests {
    #![expect(clippy::unwrap_used, reason = "a test panics on an unexpected value")]

    use std::collections::BTreeSet;
    use std::path::Path;

    use super::{UvToolConfig, get_workspace_source_names, read_uv_tool_config};
    use crate::package_name::PackageName;
    use crate::toml_access::toml_parse;

    fn doc(text: &str) -> toml_edit::DocumentMut {
        toml_parse(text, Path::new("pyproject.toml")).unwrap()
    }

    #[test]
    fn read_workspace() {
        let data = doc("[tool.uv.workspace]\nmembers = [\"packages/*\"]\nexclude = [\"packages/seeds\"]\n");
        let workspace = read_uv_tool_config(&data, Path::new("x")).unwrap().workspace;
        assert_eq!(workspace.members, vec!["packages/*"]);
        assert_eq!(workspace.exclude, vec!["packages/seeds"]);
    }

    #[test]
    fn read_defaults_without_uv_table() {
        let config = read_uv_tool_config(&doc("[project]\nname = \"foo\"\n"), Path::new("x")).unwrap();
        assert_eq!(config, UvToolConfig::default());
    }

    #[test]
    fn read_sources_keeps_only_tables() {
        let data = doc(r#"
[tool.uv.sources]
a = { workspace = true }
b = { workspace = "yes" }
c = [{ index = "one", marker = "sys_platform == 'win32'" }, { index = "two" }]
d = { git = "https://example.com/d.git" }
"#);
        let sources = read_uv_tool_config(&data, Path::new("x")).unwrap().sources;
        assert_eq!(
            sources,
            vec![
                ("a".to_owned(), true),
                ("b".to_owned(), false),
                ("c".to_owned(), false),
                ("d".to_owned(), false)
            ]
        );
    }

    #[test]
    fn workspace_source_names() {
        let data = doc(r#"
[tool.uv.sources]
Albert_Client = { workspace = true }
context = { workspace = true }
httpx = { git = "https://github.com/encode/httpx" }
local-lib = { path = "../local-lib" }
not-workspace = { workspace = false }
"#);
        assert_eq!(
            get_workspace_source_names(&data, Path::new("x")).unwrap(),
            BTreeSet::from([PackageName::new("albert-client"), PackageName::new("context")])
        );
    }

    #[test]
    fn workspace_source_names_without_sources() {
        let data = doc("[project]\nname = \"foo\"\n");
        assert!(get_workspace_source_names(&data, Path::new("x")).unwrap().is_empty());
    }
}
