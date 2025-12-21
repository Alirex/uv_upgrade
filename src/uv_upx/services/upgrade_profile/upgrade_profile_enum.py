import enum


@enum.unique
class UpgradeProfile(enum.StrEnum):
    DEFAULT = "default"
    """Default profile"""

    WITH_PINNED = "with_pinned"
    """Upgrade also "pinned" (== exact version) dependencies."""

    @staticmethod
    def get_default() -> UpgradeProfile:
        return UpgradeProfile.DEFAULT
