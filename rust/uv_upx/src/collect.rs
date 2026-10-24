//! Collect the top-level dependencies of every `pyproject.toml`: the dependency groups and their parsed items.

use std::collections::BTreeSet;
use std::fmt;
use std::path::Path;

use toml_edit::{Array, DocumentMut, Item, Value};

use crate::dependency::{DependencyParsed, parse_dependency};
use crate::error::Result;
use crate::logging;
use crate::package_name::PackageName;
use crate::path_uri::path_as_uri;
use crate::pyprojects::{PyProject, get_all_pyprojects_by_project_root_path};
use crate::toml_access::{array_strings, get_array_names_in_table, get_node, get_node_mut, is_table};
use crate::uv_tool_config::get_workspace_source_names;

const LOGGER_GROUPS: &str = "uv_upx.services.collect_dependencies.collect_groups_from_py_project";
const LOGGER_COLLECT: &str = "uv_upx.services.parse_v2.collect_dependencies";

/// Where in `pyproject.toml` a dependency list lives.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DependencySection {
    /// `project.dependencies`
    Main,
    /// `[dependency-groups]`
    DependencyGroups,
    /// `[project.optional-dependencies]`
    OptionalDependencies,
}

impl fmt::Display for DependencySection {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::Main => "project.dependencies",
            Self::DependencyGroups => "dependency-groups",
            Self::OptionalDependencies => "project.optional-dependencies",
        })
    }
}

/// One dependency list: the section and, for the grouped sections, the group name.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DependencyGroup {
    /// The section.
    pub section: DependencySection,
    /// The group name (`None` for the main dependencies).
    pub group_name: Option<String>,
}

impl DependencyGroup {
    /// `section` or `section[group]`, as the logs and the helpers command print it.
    #[must_use]
    pub fn title(&self) -> String {
        match &self.group_name {
            Some(name) => format!("{}[{name}]", self.section),
            None => self.section.to_string(),
        }
    }

    fn key_path(&self) -> Vec<&str> {
        let group = self.group_name.as_deref().unwrap_or_default();
        match self.section {
            DependencySection::Main => vec!["project", "dependencies"],
            DependencySection::DependencyGroups => vec!["dependency-groups", group],
            DependencySection::OptionalDependencies => {
                vec!["project", "optional-dependencies", group]
            }
        }
    }

    /// The array of this group in a document.
    #[must_use]
    pub fn array<'a>(&self, doc: &'a DocumentMut) -> Option<&'a Array> {
        get_node(doc, &self.key_path()).and_then(Item::as_array)
    }

    /// The editable array of this group in a document.
    #[must_use]
    pub fn array_mut<'a>(&self, doc: &'a mut DocumentMut) -> Option<&'a mut Array> {
        get_node_mut(doc, &self.key_path()).and_then(Item::as_array_mut)
    }
}

/// Python's truthiness of a TOML value: an empty array, string or table, `false` and zero are falsy.
fn is_falsy(item: &Item) -> bool {
    match item {
        Item::None => true,
        Item::Value(value) => match value {
            Value::Array(array) => array.is_empty(),
            Value::String(text) => text.value().is_empty(),
            Value::Boolean(flag) => !flag.value(),
            Value::Integer(number) => *number.value() == 0,
            Value::Float(number) => *number.value() == 0.0,
            Value::InlineTable(table) => table.is_empty(),
            Value::Datetime(_) => false,
        },
        Item::Table(table) => table.is_empty(),
        Item::ArrayOfTables(tables) => tables.is_empty(),
    }
}

/// The dependency lists of a document, in the order: main, dependency groups, optional dependencies.
#[must_use]
pub fn collect_from_py_project(doc: &DocumentMut) -> Vec<DependencyGroup> {
    let mut groups = Vec::new();

    if let Some(dependencies) = main_dependencies(doc) {
        groups.push(dependencies);
    }
    for section in [
        DependencySection::DependencyGroups,
        DependencySection::OptionalDependencies,
    ] {
        let table_path: &[&str] = match section {
            DependencySection::DependencyGroups => &["dependency-groups"],
            _ => &["project", "optional-dependencies"],
        };
        for group_name in get_array_names_in_table(doc, table_path) {
            groups.push(DependencyGroup {
                section,
                group_name: Some(group_name),
            });
        }
    }
    groups
}

fn main_dependencies(doc: &DocumentMut) -> Option<DependencyGroup> {
    let project = get_node(doc, &["project"]);
    if project.is_some() && !is_table(project) {
        logging::warning(LOGGER_GROUPS, &"No [project] table found in pyproject.toml");
        return None;
    }
    let dependencies = get_node(doc, &["project", "dependencies"])?;
    if is_falsy(dependencies) {
        return None;
    }
    if dependencies.as_array().is_none() {
        logging::warning(LOGGER_GROUPS, &"No [project].dependencies found in pyproject.toml");
        return None;
    }
    Some(DependencyGroup {
        section: DependencySection::Main,
        group_name: None,
    })
}

/// A parsed dependency and its index among the values of its array.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DependencyItemParsed {
    /// The parsed dependency.
    pub parsed: DependencyParsed,
    /// The index in the array (comments are not counted).
    pub index_in_group: usize,
}

/// A dependency list with its parsed items (nested groups and workspace members left out).
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DependencyGroupParsed {
    /// Where the list is.
    pub group: DependencyGroup,
    /// The parsed items.
    pub parsed_dependencies: Vec<DependencyItemParsed>,
}

/// A `pyproject.toml` with its parsed dependency lists.
#[derive(Clone, Debug)]
pub struct PyProjectParsed {
    /// The file.
    pub pyproject: PyProject,
    /// The lists that have at least one parsed dependency.
    pub dependency_groups_parsed: Vec<DependencyGroupParsed>,
}

/// The parsed dependencies of every `pyproject.toml` that has some.
#[derive(Clone, Debug)]
pub struct CollectedTopLevelDependencies {
    /// The files with dependencies.
    pub parsed_pyprojects: Vec<PyProjectParsed>,
}

/// How the dependencies are collected.
#[derive(Clone, Copy, Debug, Default)]
pub struct CollectOptions {
    /// Keep the names as written.
    pub preserve_original_package_names: bool,
    /// Log what is skipped.
    pub verbose: bool,
}

fn parse_group_dependencies(
    array: &Array,
    workspace_source_names: &BTreeSet<PackageName>,
    options: CollectOptions,
) -> Result<Vec<DependencyItemParsed>> {
    let mut parsed_dependencies = Vec::new();
    for (index, dependency) in array_strings(array).into_iter().enumerate() {
        let Some(dependency) = dependency else {
            if options.verbose {
                // https://docs.astral.sh/uv/concepts/projects/dependencies/#nesting-groups
                let raw = array.get(index).map(ToString::to_string).unwrap_or_default();
                logging::warning(
                    LOGGER_COLLECT,
                    &format!("Skipping non-string dependency: {}", raw.trim()),
                );
            }
            continue;
        };
        let parsed = parse_dependency(dependency, options.preserve_original_package_names)?;
        if workspace_source_names.contains(&parsed.package_name) {
            if options.verbose {
                logging::info(LOGGER_COLLECT, &format!("Skipping workspace member: {dependency}"));
            }
            continue;
        }
        parsed_dependencies.push(DependencyItemParsed {
            parsed,
            index_in_group: index,
        });
    }
    Ok(parsed_dependencies)
}

/// Collect the top-level dependencies from all `pyproject.toml` files of the project.
///
/// # Errors
///
/// When a file cannot be loaded or a dependency string does not parse.
pub fn collect_top_level_dependencies(
    project_root_path: &Path,
    options: CollectOptions,
) -> Result<CollectedTopLevelDependencies> {
    if options.verbose {
        logging::info(
            LOGGER_COLLECT,
            &format!(
                "Collect dependencies from project at: {}",
                path_as_uri(project_root_path)
            ),
        );
    }

    let py_projects = get_all_pyprojects_by_project_root_path(project_root_path)?;

    // The first item is the workspace root. Its sources apply to all members.
    let root_workspace_source_names = py_projects
        .first()
        .map(|root| get_workspace_source_names(&root.doc, &root.path))
        .transpose()?
        .unwrap_or_default();

    let mut parsed_pyprojects = Vec::new();
    for py_project in py_projects {
        let mut workspace_source_names = root_workspace_source_names.clone();
        workspace_source_names.extend(get_workspace_source_names(&py_project.doc, &py_project.path)?);

        let mut dependency_groups_parsed = Vec::new();
        for group in collect_from_py_project(&py_project.doc) {
            let Some(array) = group.array(&py_project.doc) else {
                continue;
            };
            let parsed_dependencies = parse_group_dependencies(array, &workspace_source_names, options)?;
            if parsed_dependencies.is_empty() {
                continue;
            }
            dependency_groups_parsed.push(DependencyGroupParsed {
                group,
                parsed_dependencies,
            });
        }
        if dependency_groups_parsed.is_empty() {
            continue;
        }
        parsed_pyprojects.push(PyProjectParsed {
            pyproject: py_project,
            dependency_groups_parsed,
        });
    }
    Ok(CollectedTopLevelDependencies { parsed_pyprojects })
}

#[cfg(test)]
mod tests {
    #![expect(clippy::unwrap_used, reason = "a test panics on an unexpected value")]

    use std::collections::BTreeMap;

    use super::{CollectOptions, collect_top_level_dependencies};

    #[test]
    fn workspace_members_are_skipped() {
        let tmp = tempfile::tempdir().unwrap();
        std::fs::write(
            tmp.path().join("pyproject.toml"),
            r#"
[project]
name = "root"
version = "0.1.0"
dependencies = [
    "Albert_Client",
    "context",
    "httpx>=0.24.0",
]

[tool.uv.sources]
albert-client = { workspace = true }
context = { workspace = true }

[tool.uv.workspace]
members = ["packages/*"]
"#,
        )
        .unwrap();
        let member = tmp.path().join("packages").join("context");
        std::fs::create_dir_all(&member).unwrap();
        std::fs::write(
            member.join("pyproject.toml"),
            "\n[project]\nname = \"context\"\nversion = \"0.1.0\"\ndependencies = [\n    \"albert-client\",\n    \"pydantic\",\n]\n",
        )
        .unwrap();

        let collected = collect_top_level_dependencies(tmp.path(), CollectOptions::default()).unwrap();

        let names: BTreeMap<String, Vec<String>> = collected
            .parsed_pyprojects
            .iter()
            .map(|py_project| {
                let folder = py_project.pyproject.path.parent().unwrap().file_name().unwrap();
                let deps = py_project
                    .dependency_groups_parsed
                    .iter()
                    .flat_map(|group| group.parsed_dependencies.iter())
                    .map(|dependency| dependency.parsed.package_name.to_string())
                    .collect();
                (folder.to_string_lossy().into_owned(), deps)
            })
            .collect();
        let root_name = tmp.path().file_name().unwrap().to_string_lossy().into_owned();
        assert_eq!(
            names,
            BTreeMap::from([
                (root_name, vec!["httpx".to_owned()]),
                ("context".to_owned(), vec!["pydantic".to_owned()])
            ])
        );
    }
}
