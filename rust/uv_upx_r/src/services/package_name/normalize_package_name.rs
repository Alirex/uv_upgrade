use regex::Regex;
use std::str::FromStr;

pub static PATTERN_I_NORMALIZED_I_TO_REPLACE: lazy_regex::Lazy<Regex> =
    lazy_regex::lazy_regex!(r"[-_.]+");
pub const CHAR_I_TO_USE: &str = "-";

pub type PackageNameCandidate = str;
pub type PackageNameValidated = String;

/// Normalize the package name according to PEP 503.
///
/// https://peps.python.org/pep-0503/
///
/// https://packaging.python.org/en/latest/specifications/name-normalization/
pub fn normalize_package_name(package_name: &PackageNameCandidate) -> PackageNameValidated {
    let package_name = package_name.trim();
    if package_name.is_empty() {
        panic!("Package name cannot be empty");
    }

    PATTERN_I_NORMALIZED_I_TO_REPLACE
        .replace_all(package_name, CHAR_I_TO_USE)
        .to_lowercase()
}

// Implement PackageName-like validation in Rust

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct PackageName {
    name: String,
}

impl PackageName {
    pub fn new(name: &str) -> Self {
        let normalized_name = normalize_package_name(name);
        Self {
            name: normalized_name,
        }
    }

    pub fn as_str(&self) -> &str {
        &self.name
    }
}

impl FromStr for PackageName {
    type Err = String;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        Ok(Self::new(value))
    }
}

impl From<String> for PackageName {
    fn from(value: String) -> Self {
        Self::new(&value)
    }
}

impl From<PackageName> for String {
    fn from(value: PackageName) -> Self {
        value.name
    }
}

#[cfg(test)]
mod tests;
