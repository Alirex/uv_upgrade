use clap::ValueEnum;

#[derive(Debug, Clone, Copy, PartialEq, Eq, ValueEnum)]
pub enum UpgradeProfile {
    /// Default profile
    Default,

    /// Upgrade also "pinned" (== exact version) dependencies.
    WithPinned,
}

impl UpgradeProfile {
    pub fn get_default() -> Self {
        UpgradeProfile::Default
    }
}
