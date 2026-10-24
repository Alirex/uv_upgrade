//! The dependency-string parser: a port of the Python regexes (`parse_dependency.py`).
//!
//! It is deliberately not a PEP 508 parser: markers and version texts are kept as written, because the tool writes
//! them back verbatim and the result must stay byte-identical with the Python implementation.

use std::sync::LazyLock;

use regex::Regex;

use crate::dependency::model::{DependencyParsed, Operator, VersionConstraint};
use crate::error::{Error, Result};
use crate::package_name::PackageName;

/// `===|>=|<=|==|!=|~=|<|>`: the operators, longest first.
const OPERATORS: &str = "===|>=|<=|==|!=|~=|<|>";

static PATTERN_DEPENDENCY_STRING: LazyLock<Regex> = LazyLock::new(|| {
    // Python: name, optional [extras], optional comma-separated constraints (each starting with an operator),
    // optional "; marker".
    let constraint = format!(r"(?:{OPERATORS})\s*[^,;\[]+");
    let pattern = format!(
        r"(?i)^\s*(?P<name>[A-Za-z0-9_.+-]+)\s*(?:\[(?P<extras>[^\]]+)\])?\s*(?P<version_constraints>{constraint}(?:\s*,\s*{constraint})*)?\s*(?:;\s*(?P<marker>.*))?$"
    );
    #[expect(clippy::expect_used, reason = "the pattern is a constant and covered by the tests")]
    Regex::new(&pattern).expect("valid dependency pattern")
});

static PATTERN_VERSION_CONSTRAINT: LazyLock<Regex> = LazyLock::new(|| {
    // Python builds the version class from the operator alternation, so it excludes `=`, `|`, `>`, `<`, `!`, `~`.
    let pattern = format!(r"(?i)^\s*(?P<operator>{OPERATORS})\s*(?P<version>[^=|><!~]+)\s*$");
    #[expect(clippy::expect_used, reason = "the pattern is a constant and covered by the tests")]
    Regex::new(&pattern).expect("valid version constraint pattern")
});

/// Parse a dependency string of `pyproject.toml`.
///
/// # Errors
///
/// `Error::InvalidDependency` when the string or one of its constraints does not match.
pub fn parse_dependency(dependency_string: &str, preserve_original_package_names: bool) -> Result<DependencyParsed> {
    let dependency_string = dependency_string.trim();

    let captures = PATTERN_DEPENDENCY_STRING
        .captures(dependency_string)
        .ok_or_else(|| Error::InvalidDependency(format!("Invalid dependency string: {dependency_string}")))?;

    // The name group always takes part in a match.
    let name = captures.name("name").map_or("", |m| m.as_str());

    let extras: Vec<String> = captures
        .name("extras")
        .map_or("", |m| m.as_str())
        .split(',')
        .map(str::trim)
        .filter(|item| !item.is_empty())
        .map(ToOwned::to_owned)
        .collect();

    let version_constraints =
        parse_version_constraints(captures.name("version_constraints").map_or("", |m| m.as_str()))?;

    let marker = captures
        .name("marker")
        .map(|m| m.as_str().trim())
        .filter(|marker| !marker.is_empty())
        .map(ToOwned::to_owned);

    Ok(DependencyParsed {
        original_name: preserve_original_package_names.then(|| name.to_owned()),
        package_name: PackageName::new(name),
        extras,
        version_constraints,
        marker,
    })
}

/// Parse the comma-separated constraints part, like `>=1.0, <2`.
///
/// # Errors
///
/// `Error::InvalidDependency` when a part has no operator or an invalid version text.
pub fn parse_version_constraints(version_part: &str) -> Result<Vec<VersionConstraint>> {
    let mut version_constraints = Vec::new();
    if version_part.is_empty() {
        return Ok(version_constraints);
    }
    if version_part.starts_with('@') {
        return Err(Error::InvalidDependency(format!(
            "Invalid version_part string: '{version_part}'"
        )));
    }
    for raw_part in version_part.split(',').map(str::trim).filter(|part| !part.is_empty()) {
        let captures = PATTERN_VERSION_CONSTRAINT
            .captures(raw_part)
            .ok_or_else(|| Error::InvalidDependency(format!("Invalid version constraint: '{raw_part}'")))?;
        let operator_text = captures.name("operator").map_or("", |m| m.as_str());
        let operator = Operator::parse(operator_text)
            .ok_or_else(|| Error::InvalidDependency(format!("Invalid version operator: '{operator_text}'")))?;
        let version = captures.name("version").map_or("", |m| m.as_str());
        let constraint = VersionConstraint::new(operator, version)
            .map_err(|detail| Error::InvalidDependency(format!("{detail}: '{raw_part}'")))?;
        version_constraints.push(constraint);
    }
    Ok(version_constraints)
}

#[cfg(test)]
mod tests {
    #![expect(clippy::unwrap_used, reason = "a test panics on an unexpected value")]

    use super::parse_dependency;
    use crate::dependency::model::{DependencyParsed, Operator, VersionConstraint};
    use crate::package_name::PackageName;

    fn constraint(operator: Operator, version: &str) -> VersionConstraint {
        VersionConstraint {
            operator,
            version: version.to_owned(),
        }
    }

    fn multi(marker: &str) -> DependencyParsed {
        DependencyParsed {
            original_name: None,
            package_name: PackageName::new("foo"),
            extras: vec!["bla".to_owned(), "xyz".to_owned()],
            version_constraints: vec![
                constraint(Operator::GreaterOrEqual, "32.0"),
                constraint(Operator::NotEqual, "33"),
                constraint(Operator::Less, "34"),
            ],
            marker: Some(marker.to_owned()),
        }
    }

    #[test]
    fn only_name() {
        let result = parse_dependency("foo", false).unwrap();
        assert_eq!(result, DependencyParsed::new(PackageName::new("foo")));
    }

    #[test]
    fn simple_greater_or_equal() {
        let result = parse_dependency("foo>=32.0", false).unwrap();
        let mut expected = DependencyParsed::new(PackageName::new("foo"));
        expected.version_constraints = vec![constraint(Operator::GreaterOrEqual, "32.0")];
        assert_eq!(result, expected);
    }

    #[test]
    fn simple_less_or_equal() {
        let result = parse_dependency("foo<=32.0", false).unwrap();
        let mut expected = DependencyParsed::new(PackageName::new("foo"));
        expected.version_constraints = vec![constraint(Operator::LessOrEqual, "32.0")];
        assert_eq!(result, expected);
    }

    #[test]
    fn multiple_constraints() {
        let result = parse_dependency("foo[bla,xyz]>=32.0,!=33,<34;python_version<'3.11'", false).unwrap();
        assert_eq!(result, multi("python_version<'3.11'"));
    }

    #[test]
    fn multiple_constraints_with_spaces() {
        let result = parse_dependency(r#"foo[bla,xyz] >=32.0, !=33, <34 ;python_version<"3.11""#, false).unwrap();
        assert_eq!(result, multi(r#"python_version<"3.11""#));
    }

    #[test]
    fn invalid_strings() {
        assert!(parse_dependency("foo @ https://example.com/foo.whl", false).is_err());
        assert!(parse_dependency("foo>=v1", false).is_err());
        assert!(parse_dependency("", false).is_err());
    }

    #[test]
    fn preserve_original_name() {
        let result = parse_dependency("Foo_Bar[Dev]>=1", true).unwrap();
        assert_eq!(result.original_name.as_deref(), Some("Foo_Bar"));
        assert_eq!(result.package_name, PackageName::new("foo-bar"));
        assert_eq!(result.get_full_spec(), "Foo_Bar[Dev]>=1");
    }
}
