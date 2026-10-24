//! `uv-upx helpers collect-top-level-dependencies-from-project`: print the dependencies of every `pyproject.toml`.

use std::io::Write;
use std::path::Path;

use crate::collect::collect_from_py_project;
use crate::dependency::{DependencyParsed, parse_dependency};
use crate::error::Result;
use crate::logging;
use crate::path_uri::path_as_uri;
use crate::pyprojects::get_all_pyprojects_by_project_root_path;
use crate::toml_access::array_strings;

const LOGGER: &str = "uv_upx.services.collect_top_level_dependencies.collect_top_level_dependencies";
const TAB_CHARS: &str = "  ";

/// Options of the helpers command.
#[derive(Clone, Copy, Debug, Default)]
pub struct CollectTopLevelOptions {
    /// Print only ranges, missing bounds, pinned and unhandled constraints.
    pub only_special_cases: bool,
    /// Keep the names as written.
    pub preserve_original_package_names: bool,
}

/// A dependency is "special" when it has a marker, several constraints, none, or an operator other than `>=`.
fn is_special_case(dependency: &DependencyParsed) -> bool {
    dependency.marker.is_some()
        || dependency.version_constraints.len() != 1
        || dependency
            .version_constraints
            .iter()
            .any(|constraint| !constraint.operator.is_put_if_different())
}

/// Parse the strings of a dependency list and keep the ones to print.
///
/// Like the Python version, nothing is printed without `--only-special-cases` (every string is still parsed).
///
/// # Errors
///
/// When a dependency string does not parse.
pub fn filter_dependencies(
    dependencies: &[Option<&str>],
    options: CollectTopLevelOptions,
) -> Result<Vec<DependencyParsed>> {
    let mut selected = Vec::new();
    for dependency in dependencies.iter().flatten() {
        let parsed = parse_dependency(dependency, options.preserve_original_package_names)?;
        if options.only_special_cases && is_special_case(&parsed) {
            selected.push(parsed);
        }
    }
    Ok(selected)
}

/// Print the collected dependencies to `out` (stdout in the CLI).
///
/// # Errors
///
/// When a file cannot be loaded, a dependency string does not parse, or writing fails.
pub fn collect_top_level_dependencies(
    project_root_path: &Path,
    options: CollectTopLevelOptions,
    out: &mut dyn Write,
) -> Result<()> {
    logging::info(LOGGER, &"Collecting top level dependencies...");

    let py_projects = get_all_pyprojects_by_project_root_path(project_root_path)?;

    for py_project in &py_projects {
        let mut is_py_project_info_shown = false;

        for group in collect_from_py_project(&py_project.doc) {
            let Some(array) = group.array(&py_project.doc) else {
                continue;
            };
            let mut is_group_title_shown = false;

            for dependency in filter_dependencies(&array_strings(array), options)? {
                if !is_py_project_info_shown {
                    write_line(out, &path_as_uri(&py_project.path))?;
                    is_py_project_info_shown = true;
                }
                if !is_group_title_shown {
                    write_line(out, &format!("{TAB_CHARS}{}:", group.title()))?;
                    is_group_title_shown = true;
                }
                write_line(out, &format!("{TAB_CHARS}{TAB_CHARS}{}", dependency.get_full_spec()))?;
            }

            if is_group_title_shown {
                write_line(out, &"-".repeat(10))?;
            }
        }

        if is_py_project_info_shown {
            write_line(out, &"=".repeat(20))?;
        }
    }

    logging::info(LOGGER, &"Done.");
    Ok(())
}

fn write_line(out: &mut dyn Write, line: &str) -> Result<()> {
    writeln!(out, "{line}").map_err(|source| crate::error::Error::Io {
        action: "Failed to write",
        path: std::path::PathBuf::from("<stdout>"),
        source,
    })
}
