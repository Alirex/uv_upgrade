use super::*;
use crate::services::updater::updater_options::UpdaterOptions;
use clap::Parser;
use std::path::PathBuf;

#[test]
fn parse_many_flags() {
    let args = [
        "uv-upx",
        "upgrade",
        "--verbose",
        "--profile",
        "default",
        "--project",
        "/tmp",
        "--preserve-original-package-names",
        "--no-sync",
        "--interactive",
    ];

    let cli = Cli::try_parse_from(&args).expect("should parse args");

    let upgrade_args = match cli.command {
        CommandsTop::Upgrade(args) => args,
        _ => panic!("Expected Upgrade command"),
    };

    assert!(upgrade_args.verbose);
    assert_eq!(upgrade_args.profile.unwrap(), UpgradeProfile::Default);
    assert!(upgrade_args.preserve_original_package_names);
    assert!(upgrade_args.no_sync);
    assert!(upgrade_args.interactive);
    assert_eq!(
        upgrade_args.project_root_path.clone().unwrap(),
        PathBuf::from("/tmp")
    );

    let opts: UpdaterOptions = upgrade_args.into();
    assert_eq!(opts.dry_run, false);
    assert!(opts.verbose);
    assert_eq!(opts.profile, UpgradeProfile::Default);
    assert_eq!(opts.project_root.unwrap(), PathBuf::from("/tmp"));
}

#[test]
fn defaults_when_no_profile() {
    let args = ["uv-upx", "upgrade"];
    let cli = Cli::try_parse_from(&args).expect("should parse empty args");

    let upgrade_args = match cli.command {
        CommandsTop::Upgrade(args) => args,
        _ => panic!("Expected Upgrade command"),
    };

    let opts: UpdaterOptions = upgrade_args.into();
    assert_eq!(opts.profile, UpgradeProfile::Default);
}
