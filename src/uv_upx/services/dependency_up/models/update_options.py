from dataclasses import dataclass

from uv_upx.services.upgrade_profile import UpgradeProfile


@dataclass(frozen=True, kw_only=True)
class DependencyUpdateOptions:
    """What an upgrade may change in a dependency string."""

    profile: UpgradeProfile = UpgradeProfile.DEFAULT
    #
    keep_unconstrained: bool = False
    """Leave dependencies written without a version constraint as they are."""
