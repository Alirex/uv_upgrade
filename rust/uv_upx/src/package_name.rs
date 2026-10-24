//! Package names normalized per PEP 503 (<https://packaging.python.org/en/latest/specifications/name-normalization/>).

use std::fmt;

/// Normalize a package name: runs of `-`, `_` and `.` become one `-`, letters become lowercase.
#[must_use]
pub fn normalize_package_name(package_name: &str) -> String {
    let mut out = String::with_capacity(package_name.len());
    let mut in_separator = false;
    for ch in package_name.chars() {
        if matches!(ch, '-' | '_' | '.') {
            if !in_separator {
                out.push('-');
                in_separator = true;
            }
        } else {
            in_separator = false;
            out.extend(ch.to_lowercase());
        }
    }
    out
}

/// A normalized package name. Two spellings of one package compare equal.
#[derive(Clone, Debug, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct PackageName(String);

impl PackageName {
    /// Normalize a raw name.
    #[must_use]
    pub fn new(raw: &str) -> Self {
        Self(normalize_package_name(raw))
    }

    /// The normalized name.
    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl fmt::Display for PackageName {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

#[cfg(test)]
mod tests {
    use std::collections::HashMap;

    use super::{PackageName, normalize_package_name};

    #[test]
    fn package_name_normalization() {
        for (package_name, expected) in [
            ("foo", "foo"),
            ("Foo", "foo"),
            ("FoO", "foo"),
            ("FoO-bar", "foo-bar"),
            ("FoO_bar", "foo-bar"),
            ("TOMLKit", "tomlkit"),
            ("Pydantic", "pydantic"),
            ("pyTEST_BenchMark", "pytest-benchmark"),
        ] {
            assert_eq!(normalize_package_name(package_name), expected, "{package_name}");
        }
    }

    #[test]
    fn package_name_equal_and_hashable() {
        assert_eq!(PackageName::new("Foo_Bar"), PackageName::new("foo-bar"));
        assert_eq!(PackageName::new("Foo_Bar"), PackageName::new("foo.bar"));
        let map = HashMap::from([(PackageName::new("foo-bar"), 1)]);
        assert_eq!(map[&PackageName::new("FOO_BAR")], 1);
    }
}
