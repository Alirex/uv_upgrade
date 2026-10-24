from dataclasses import dataclass

from uv_upx.services.upgrade_profile import UpgradeProfile


@dataclass(frozen=True, kw_only=True)
class UpdaterOptions:
    """Switches of one `run_updater` call."""

    dry_run: bool = False
    verbose: bool = False
    #
    preserve_original_package_names: bool = False
    #
    no_sync: bool = False
    #
    interactive: bool = False
    #
    keep_unconstrained: bool = False
    """Leave dependencies written without a version constraint as they are."""
    #
    profile: UpgradeProfile = UpgradeProfile.DEFAULT
