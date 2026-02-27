use crate::cli::args::UpgradeArgs;
use crate::services::upgrade_profile::upgrade_profile_enum::UpgradeProfile;
use std::path::PathBuf;

/// Options passed to the updater shim in Rust.
#[derive(Debug)]
pub struct UpdaterOptions {
    pub project_root: Option<PathBuf>,
    pub dry_run: bool,
    pub verbose: bool,
    pub preserve_original_package_names: bool,
    pub no_sync: bool,
    pub interactive: bool,
    pub profile: UpgradeProfile,
}

impl From<UpgradeArgs> for UpdaterOptions {
    fn from(cli: UpgradeArgs) -> Self {
        UpdaterOptions {
            project_root: cli.project_root_path,
            dry_run: false,
            verbose: cli.verbose,
            preserve_original_package_names: cli.preserve_original_package_names,
            no_sync: cli.no_sync,
            interactive: cli.interactive,
            profile: cli.profile.unwrap_or_else(UpgradeProfile::get_default),
        }
    }
}
