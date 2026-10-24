//! Move the constraints of one dependency to the locked version.

use crate::UpgradeProfile;
use crate::dependency::model::{ChangesItem, DependencyParsed, Operator, VersionConstraint};
use crate::logging;
use crate::uv_lock::DependenciesRegistry;

const LOGGER: &str = "uv_upx.services.dependency_up.update_dependency";

/// What an upgrade may change in a dependency string.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct DependencyUpdateOptions {
    /// Which operators move.
    pub profile: UpgradeProfile,
    /// Leave dependencies written without a version constraint as they are.
    pub keep_unconstrained: bool,
}

/// Update the constraints of `parsed` in place from the registry.
///
/// A dependency without a version constraint gets `>=<locked version>`, unless `options.keep_unconstrained` is set.
/// Returns the change, or `None` when nothing changed (also when the package is not in the registry: an error is
/// logged).
#[must_use]
pub fn update_dependency(
    dependencies_registry: &DependenciesRegistry,
    parsed: &mut DependencyParsed,
    options: DependencyUpdateOptions,
) -> Option<ChangesItem> {
    let Some(version_new) = dependencies_registry.get(&parsed.package_name) else {
        logging::error(
            LOGGER,
            &format!("Dependency not found in the registry: {}", parsed.package_name),
        );
        return None;
    };

    let parsed_original = parsed.clone();
    let mut is_has_changes = false;
    for version_constraint in &mut parsed.version_constraints {
        if handle_version_constraint(version_constraint, version_new, options.profile) {
            is_has_changes = true;
        }
    }

    if parsed.version_constraints.is_empty() {
        if options.keep_unconstrained {
            return None;
        }
        parsed.version_constraints.push(VersionConstraint {
            operator: Operator::GreaterOrEqual,
            version: version_new.to_owned(),
        });
        is_has_changes = true;
    }

    is_has_changes.then(|| ChangesItem {
        from_item: parsed_original,
        to_item: parsed.clone(),
    })
}

/// Move one constraint to `version_new` when its operator allows it. Returns whether it changed.
#[must_use]
pub fn handle_version_constraint(
    version_constraint: &mut VersionConstraint,
    version_new: &str,
    profile: UpgradeProfile,
) -> bool {
    let movable = version_constraint.operator.is_put_if_different()
        || (profile == UpgradeProfile::WithPinned && version_constraint.operator.is_pinned_allowed_to_change());
    if movable && version_constraint.version != version_new {
        version_new.clone_into(&mut version_constraint.version);
        return true;
    }
    false
}

#[cfg(test)]
mod tests {
    #![expect(clippy::unwrap_used, reason = "a test panics on an unexpected value")]

    use super::{DependencyUpdateOptions, handle_version_constraint, update_dependency};
    use crate::UpgradeProfile;
    use crate::dependency::model::{Operator, VersionConstraint};
    use crate::dependency::parse::parse_dependency;
    use crate::uv_lock::DependenciesRegistry;

    fn registry() -> DependenciesRegistry {
        DependenciesRegistry::from_pairs([("httpx", "0.28.1"), ("pydantic", "2.12.5")])
    }

    #[test]
    fn update_dependency_cases() {
        let cases: [(&str, UpgradeProfile, Option<&str>); 7] = [
            ("httpx>=0.24.0", UpgradeProfile::Default, Some("httpx>=0.28.1")),
            ("httpx", UpgradeProfile::Default, Some("httpx>=0.28.1")),
            (
                r#"httpx[http2]>=0.24.0; python_version >= "3.14""#,
                UpgradeProfile::Default,
                Some(r#"httpx[http2]>=0.28.1; python_version >= "3.14""#),
            ),
            ("httpx>=0.24.0,<1", UpgradeProfile::Default, Some("httpx>=0.28.1,<1")),
            ("pydantic==2.0.0", UpgradeProfile::Default, None),
            ("pydantic==2.0.0", UpgradeProfile::WithPinned, Some("pydantic==2.12.5")),
            ("pydantic>=2.12.5", UpgradeProfile::Default, None),
        ];
        for (dependency, profile, expected) in cases {
            let mut parsed = parse_dependency(dependency, false).unwrap();
            let options = DependencyUpdateOptions {
                profile,
                keep_unconstrained: false,
            };
            let change = update_dependency(&registry(), &mut parsed, options);
            match expected {
                None => assert!(change.is_none(), "{dependency}"),
                Some(expected) => {
                    let change = change.unwrap();
                    assert_eq!(
                        change.from_item.get_full_spec(),
                        parse_dependency(dependency, false).unwrap().get_full_spec()
                    );
                    assert_eq!(change.to_item.get_full_spec(), expected);
                }
            }
        }
    }

    #[test]
    fn update_dependency_keep_unconstrained() {
        let cases = [
            ("httpx", None),
            (r#"httpx[http2]; python_version >= "3.14""#, None),
            ("httpx>=0.24.0", Some("httpx>=0.28.1")),
        ];
        for (dependency, expected) in cases {
            let mut parsed = parse_dependency(dependency, false).unwrap();
            let options = DependencyUpdateOptions {
                profile: UpgradeProfile::Default,
                keep_unconstrained: true,
            };
            let change = update_dependency(&registry(), &mut parsed, options);
            assert_eq!(
                change.map(|c| c.to_item.get_full_spec()),
                expected.map(ToOwned::to_owned)
            );
        }
    }

    #[test]
    fn update_dependency_not_in_registry() {
        let mut parsed = parse_dependency("unknown>=1.0", false).unwrap();
        assert!(update_dependency(&registry(), &mut parsed, DependencyUpdateOptions::default()).is_none());
    }

    #[test]
    fn handle_version_constraint_cases() {
        let cases = [
            (Operator::GreaterOrEqual, ">=33.1"),
            (Operator::Greater, ">32.0"),
            (Operator::Equal, "==32.0"),
            (Operator::Less, "<32.0"),
        ];
        for (operator, expected) in cases {
            let mut constraint = VersionConstraint {
                operator,
                version: "32.0".to_owned(),
            };
            let _ = handle_version_constraint(&mut constraint, "33.1", UpgradeProfile::Default);
            assert_eq!(constraint.to_string(), expected);
        }
    }
}
