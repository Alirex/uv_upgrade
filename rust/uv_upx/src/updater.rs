//! The upgrade flow: `uv lock --upgrade`, rewrite the `pyproject.toml` files from the new lock, sync; roll back on
//! any failure, on "no changes" and on `--dry-run`.

use std::path::{Path, PathBuf};

use crate::UpgradeProfile;
use crate::collect::{CollectOptions, CollectedTopLevelDependencies, collect_top_level_dependencies};
use crate::dependency::{ChangesItem, DependencyUpdateOptions, update_dependency};
use crate::error::{Error, Result, read_text, write_text};
use crate::interactive::{ask_interactive_confirmation, show_interactive_information};
use crate::logging;
use crate::path_uri::path_as_uri;
use crate::paths::get_and_check_path_to_uv_lock;
use crate::pinned::change_pinned_constraints;
use crate::pyprojects::{PyProject, get_all_pyprojects_by_project_root_path};
use crate::toml_access::set_array_string;
use crate::uv_lock::{DependenciesRegistry, get_dependencies_from_project};
use crate::uv_runner::{UvSyncMode, run_uv_lock, run_uv_sync};

const LOGGER_RUN: &str = "uv_upx.services.updater.run_updater";
const LOGGER_ROLLBACK: &str = "uv_upx.services.updater.rollback_updater";
const LOGGER_FINALIZE: &str = "uv_upx.services.updater.finalize_updating";
const LOGGER_GROUPS: &str = "uv_upx.services.dependency_up.handle_groups";

const LOCAL_SEGMENTS_MESSAGE: &str = "Cannot proceed with pinned profile because there are local segments present. \
                                      We rollback and try again with pinning constraints with local segments.";

/// Switches of one `run_updater` call.
#[derive(Clone, Copy, Debug, Default)]
#[expect(clippy::struct_excessive_bools, reason = "one independent CLI flag per field")]
pub struct UpdaterOptions {
    /// Roll back at the end; show what would change.
    pub dry_run: bool,
    /// Log more.
    pub verbose: bool,
    /// Keep the names as written.
    pub preserve_original_package_names: bool,
    /// Relock with `uv lock` instead of `uv sync`.
    pub no_sync: bool,
    /// Ask before each change.
    pub interactive: bool,
    /// Leave dependencies written without a version constraint as they are.
    pub keep_unconstrained: bool,
    /// Which operators move.
    pub profile: UpgradeProfile,
}

impl UpdaterOptions {
    const fn update_options(self) -> DependencyUpdateOptions {
        DependencyUpdateOptions {
            profile: self.profile,
            keep_unconstrained: self.keep_unconstrained,
        }
    }
}

/// What the rollback writes back.
struct RollbackData {
    uv_lock_path: PathBuf,
    uv_lock_text: String,
    py_projects: Vec<PyProject>,
}

fn rollback_updater(rollback_data: &RollbackData, no_sync: bool) -> Result<()> {
    write_text(&rollback_data.uv_lock_path, &rollback_data.uv_lock_text)?;
    for py_project in &rollback_data.py_projects {
        py_project.restore()?;
    }
    if !no_sync {
        let workdir = rollback_data.uv_lock_path.parent().unwrap_or(Path::new("."));
        run_uv_sync(workdir, UvSyncMode::Frozen, true)?;
    }
    logging::info(LOGGER_ROLLBACK, &"Rollback completed.");
    Ok(())
}

fn update_lock_file(project_root_path: &Path) -> Result<()> {
    // A fast update, without triggering a build for now.
    run_uv_lock(project_root_path, true)
}

fn update_lock_file_with_fallback(
    project_root_path: &Path,
    collected: &CollectedTopLevelDependencies,
    rollback_data: &RollbackData,
    options: UpdaterOptions,
) -> Result<()> {
    match update_lock_file(project_root_path) {
        Ok(()) => Ok(()),
        Err(Error::NonEmptyLocalSegments) => {
            // Workaround for dependencies with local segments.
            logging::error(LOGGER_RUN, &LOCAL_SEGMENTS_MESSAGE);
            rollback_updater(rollback_data, options.no_sync)?;
            change_pinned_constraints(collected, true)?;
            update_lock_file(project_root_path)
        }
        Err(error) => Err(error),
    }
}

fn handle_py_projects(
    dependencies_registry: &DependenciesRegistry,
    collected: &mut CollectedTopLevelDependencies,
    options: UpdaterOptions,
) -> Result<Vec<ChangesItem>> {
    let mut changes = Vec::new();
    if options.interactive {
        show_interactive_information();
    }
    for py_project in &mut collected.parsed_pyprojects {
        let mut changes_local = Vec::new();
        let path_uri = path_as_uri(&py_project.pyproject.path);

        for group in &mut py_project.dependency_groups_parsed {
            for dependency in &mut group.parsed_dependencies {
                let mut candidate = dependency.parsed.clone();
                let Some(change) = update_dependency(dependencies_registry, &mut candidate, options.update_options())
                else {
                    continue;
                };
                let apply_change = if options.interactive {
                    ask_interactive_confirmation(&change, &group.group, &py_project.pyproject.path)?
                } else {
                    true
                };
                if apply_change {
                    if let Some(array) = group.group.array_mut(&mut py_project.pyproject.doc) {
                        set_array_string(array, dependency.index_in_group, &candidate.get_full_spec());
                    }
                    dependency.parsed = candidate;
                    changes_local.push(change);
                } else if options.verbose {
                    logging::info(
                        LOGGER_GROUPS,
                        &format!("Skipped change for {} in {path_uri}", dependency.parsed.package_name),
                    );
                }
            }
        }

        if !changes_local.is_empty() || options.profile == UpgradeProfile::WithPinned {
            // The pinned profile rewrote `==` to `>=` on disk: the document must be written back even without changes.
            py_project.pyproject.save()?;
            logging::info(LOGGER_GROUPS, &format!("Saved changes to {path_uri}"));
            for change in &changes_local {
                logging::info(LOGGER_GROUPS, &format!("  {change}"));
            }
        }
        changes.extend(changes_local);
    }
    Ok(changes)
}

fn finalize_updating(project_root_path: &Path, options: UpdaterOptions) -> Result<()> {
    if options.dry_run {
        logging::info(LOGGER_FINALIZE, &"Dry run. No changes were made.");
        return Ok(());
    }
    if options.profile == UpgradeProfile::WithPinned || options.interactive {
        let uv_lock_path = get_and_check_path_to_uv_lock(project_root_path)?;
        if let Err(source) = std::fs::remove_file(&uv_lock_path)
            && source.kind() != std::io::ErrorKind::NotFound
        {
            return Err(Error::Io {
                action: "Failed to remove",
                path: uv_lock_path,
                source,
            });
        }
    }
    if options.no_sync {
        run_uv_lock(project_root_path, false)?;
        logging::info(LOGGER_FINALIZE, &"Updated uv.lock successfully.");
    } else {
        // Because we want to re-check that all is ok.
        run_uv_sync(project_root_path, UvSyncMode::Default, true)?;
        logging::info(
            LOGGER_FINALIZE,
            &"Synced dependencies successfully with updating uv.lock.",
        );
    }
    Ok(())
}

/// Update the lock file and the `pyproject.toml` files. `Ok(false)` when there are no important changes.
fn apply_updates(
    project_root_path: &Path,
    collected: &mut CollectedTopLevelDependencies,
    rollback_data: &RollbackData,
    options: UpdaterOptions,
) -> Result<bool> {
    update_lock_file_with_fallback(project_root_path, collected, rollback_data, options)?;

    let dependencies_registry = get_dependencies_from_project(project_root_path)?;

    if handle_py_projects(&dependencies_registry, collected, options)?.is_empty() {
        return Ok(false);
    }
    logging::info(LOGGER_RUN, &"Updated pyproject.toml files successfully.");

    finalize_updating(project_root_path, options)?;
    Ok(true)
}

/// Orchestrate the dependency update with a rollback on failure.
///
/// Like the Python version, a failure after the start of the update (a failing `uv lock` or `uv sync`) is logged
/// and rolled back, and the call still returns `Ok`.
///
/// # Errors
///
/// When the project cannot be read before the update starts: a missing `uv.lock` or `pyproject.toml`, invalid TOML,
/// an invalid dependency string.
pub fn run_updater(project_root_path: &Path, options: UpdaterOptions) -> Result<()> {
    let uv_lock_path = get_and_check_path_to_uv_lock(project_root_path)?;
    let uv_lock_text = read_text(&uv_lock_path)?;

    let py_projects = get_all_pyprojects_by_project_root_path(project_root_path)?;
    if options.verbose {
        logging::info(
            LOGGER_RUN,
            &format!("Found {} pyproject.toml files in the workspace.", py_projects.len()),
        );
        for py_project in &py_projects {
            logging::info(LOGGER_RUN, &format!("  {}", path_as_uri(&py_project.path)));
        }
    }

    let rollback_data = RollbackData {
        uv_lock_path,
        uv_lock_text,
        py_projects,
    };

    let mut collected = collect_top_level_dependencies(
        project_root_path,
        CollectOptions {
            preserve_original_package_names: options.preserve_original_package_names,
            verbose: false,
        },
    )?;

    if options.profile == UpgradeProfile::WithPinned {
        change_pinned_constraints(&collected, false)?;
    }

    let mut rollback_message: Option<String> = None;
    match apply_updates(project_root_path, &mut collected, &rollback_data, options) {
        Ok(true) => {}
        Ok(false) => {
            let message = "No important changes detected. Rolling back to previous state.";
            logging::info(LOGGER_RUN, &message);
            rollback_message = Some(message.to_owned());
        }
        Err(error) => {
            let message = format!(
                "Failed to update dependencies: '{}:{error}' Rolling back to previous state.",
                error.python_type()
            );
            logging::error(LOGGER_RUN, &message);
            rollback_message = Some(message);
        }
    }
    if options.dry_run {
        rollback_message = Some("Dry run enabled, rolling back to previous state.".to_owned());
    }

    if let Some(message) = rollback_message {
        match rollback_updater(&rollback_data, options.no_sync) {
            Ok(()) => logging::info(LOGGER_RUN, &message),
            Err(error) => logging::error(LOGGER_RUN, &format!("Failed to rollback: '{error}'")),
        }
    }
    Ok(())
}
