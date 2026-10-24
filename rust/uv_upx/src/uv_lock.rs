//! The locked versions: the `[[package]]` entries of `uv.lock` (the source of truth for the upgrade).

use std::collections::BTreeMap;
use std::path::Path;

use toml_edit::{Item, TableLike};

use crate::error::{Error, Result, read_text};
use crate::package_name::PackageName;
use crate::paths::get_and_check_path_to_uv_lock;
use crate::toml_access::toml_parse;

/// Package name to locked version.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct DependenciesRegistry(BTreeMap<PackageName, String>);

impl DependenciesRegistry {
    /// A registry from `(name, version)` pairs (names are normalized).
    pub fn from_pairs<'a>(pairs: impl IntoIterator<Item = (&'a str, &'a str)>) -> Self {
        Self(
            pairs
                .into_iter()
                .map(|(name, version)| (PackageName::new(name), version.to_owned()))
                .collect(),
        )
    }

    /// The locked version of a package.
    #[must_use]
    pub fn get(&self, name: &PackageName) -> Option<&str> {
        self.0.get(name).map(String::as_str)
    }

    /// Name to version, sorted by name.
    #[must_use]
    pub const fn as_map(&self) -> &BTreeMap<PackageName, String> {
        &self.0
    }
}

/// Parse the text of a `uv.lock`. Packages without a version (like a dynamic-version editable) are skipped.
///
/// # Errors
///
/// `Error::Toml` when the text does not parse, `Error::Validation` when a package has no string name.
pub fn parse_from_uv_lock_file(content: &str, path: &Path) -> Result<DependenciesRegistry> {
    let doc = toml_parse(content, path)?;
    let mut registry = DependenciesRegistry::default();
    let Some(packages) = doc.get("package") else {
        return Ok(registry);
    };
    let tables: Vec<&dyn TableLike> = match packages {
        Item::ArrayOfTables(tables) => tables.iter().map(|table| table as &dyn TableLike).collect(),
        Item::Value(value) => value
            .as_array()
            .map(|array| {
                array
                    .iter()
                    .filter_map(|value| value.as_inline_table().map(|t| t as &dyn TableLike))
                    .collect()
            })
            .unwrap_or_default(),
        Item::None | Item::Table(_) => Vec::new(),
    };
    for table in tables {
        let name = table
            .get("name")
            .and_then(Item::as_str)
            .ok_or_else(|| Error::Validation {
                path: path.to_path_buf(),
                detail: "a [[package]] entry has no string `name`".to_owned(),
            })?;
        match table.get("version") {
            None => {}
            Some(version) => {
                let version = version.as_str().ok_or_else(|| Error::Validation {
                    path: path.to_path_buf(),
                    detail: format!("package {name}: `version` is not a string"),
                })?;
                registry.0.insert(PackageName::new(name), version.to_owned());
            }
        }
    }
    Ok(registry)
}

/// Read `<workdir>/uv.lock`.
///
/// # Errors
///
/// When the file is missing, unreadable or invalid.
pub fn get_dependencies_from_project(workdir: &Path) -> Result<DependenciesRegistry> {
    let path = get_and_check_path_to_uv_lock(workdir)?;
    parse_from_uv_lock_file(&read_text(&path)?, &path)
}

#[cfg(test)]
mod tests {
    #![expect(clippy::unwrap_used, reason = "a test panics on an unexpected value")]

    use std::path::Path;

    use super::{DependenciesRegistry, parse_from_uv_lock_file};

    #[test]
    fn parse_from_uv_lock_file_skips_packages_without_version() {
        let registry = parse_from_uv_lock_file(
            r#"
version = 1

[[package]]
name = "Typing_Extensions"
version = "4.15.0"

[[package]]
name = "pydantic"
version = "2.12.5"

[[package]]
name = "dynamic-version"
source = { editable = "." }
"#,
            Path::new("uv.lock"),
        )
        .unwrap();
        assert_eq!(
            registry,
            DependenciesRegistry::from_pairs([("typing-extensions", "4.15.0"), ("pydantic", "2.12.5")])
        );
    }
}
