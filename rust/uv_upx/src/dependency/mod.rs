//! One dependency string of `pyproject.toml`: its parts, how it is parsed and how its constraints are updated.

pub mod model;
pub mod parse;
pub mod update;

pub use model::{ChangesItem, DependencyParsed, Operator, VersionConstraint};
pub use parse::parse_dependency;
pub use update::{DependencyUpdateOptions, handle_version_constraint, update_dependency};
