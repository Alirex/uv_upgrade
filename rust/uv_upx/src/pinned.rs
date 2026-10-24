//! Rewrite pinned constraints on disk before `uv lock --upgrade` (the `with_pinned` profile and the local-segment
//! fallback). The in-memory collection is left as it is, like the Python version: it is written back afterwards.

use crate::collect::CollectedTopLevelDependencies;
use crate::dependency::Operator;
use crate::error::Result;
use crate::toml_access::set_array_string;

/// Marks a local segment in a version, like `1.0.0+foo`.
pub const LOCAL_SEGMENT_CHAR_INDICATOR: char = '+';

/// Change `==` constraints to `>=` in the files, so that `uv lock --upgrade` may move them.
///
/// With `is_ignore_local_segments`, `>=` constraints on versions with a local segment become `==` instead (uv
/// rejects `>=` on such versions).
///
/// # Errors
///
/// When a file cannot be written.
pub fn change_pinned_constraints(
    collected_top_level_dependencies: &CollectedTopLevelDependencies,
    is_ignore_local_segments: bool,
) -> Result<()> {
    let mut copied = collected_top_level_dependencies.clone();

    for py_project in &mut copied.parsed_pyprojects {
        let mut is_have_changes_for_file = false;

        for group in &mut py_project.dependency_groups_parsed {
            for dependency in &mut group.parsed_dependencies {
                let dependency_parsed = &mut dependency.parsed;

                let mut is_have_changes_for_dependency = false;
                for version_constraint in &mut dependency_parsed.version_constraints {
                    if is_ignore_local_segments
                        && version_constraint.operator.is_put_if_different()
                        && version_constraint.version.contains(LOCAL_SEGMENT_CHAR_INDICATOR)
                    {
                        version_constraint.operator = Operator::Equal;
                        is_have_changes_for_dependency = true;
                    } else if version_constraint.operator.is_pinned_allowed_to_change() {
                        version_constraint.operator = Operator::GreaterOrEqual;
                        is_have_changes_for_dependency = true;
                    }
                }

                if is_have_changes_for_dependency {
                    if let Some(array) = group.group.array_mut(&mut py_project.pyproject.doc) {
                        set_array_string(array, dependency.index_in_group, &dependency_parsed.get_full_spec());
                    }
                    is_have_changes_for_file = true;
                }
            }
        }

        if is_have_changes_for_file {
            py_project.pyproject.save()?;
        }
    }
    Ok(())
}
