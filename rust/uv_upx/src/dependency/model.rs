//! The parts of a dependency string (PEP 508) as this tool sees them.

use std::fmt;

use crate::package_name::PackageName;

/// A version operator (PEP 440 version specifiers).
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Operator {
    /// `>=`: the lower bound this tool moves.
    GreaterOrEqual,
    /// `==`: pinned; moved only by the `with_pinned` profile.
    Equal,
    /// `===`: arbitrary equality; never touched.
    ArbitraryEqual,
    /// `<`
    Less,
    /// `<=`
    LessOrEqual,
    /// `~=`
    Compatible,
    /// `>`
    Greater,
    /// `!=`
    NotEqual,
}

impl Operator {
    /// All operators, longest first (the order the parser tries them in).
    pub const ALL: [Self; 8] = [
        Self::ArbitraryEqual,
        Self::GreaterOrEqual,
        Self::LessOrEqual,
        Self::Equal,
        Self::NotEqual,
        Self::Compatible,
        Self::Less,
        Self::Greater,
    ];

    /// The operator text.
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::GreaterOrEqual => ">=",
            Self::Equal => "==",
            Self::ArbitraryEqual => "===",
            Self::Less => "<",
            Self::LessOrEqual => "<=",
            Self::Compatible => "~=",
            Self::Greater => ">",
            Self::NotEqual => "!=",
        }
    }

    /// The operator of a text, if it is one.
    #[must_use]
    pub fn parse(text: &str) -> Option<Self> {
        Self::ALL.into_iter().find(|operator| operator.as_str() == text)
    }

    /// The version is replaced when it differs from the locked one (`>=`).
    #[must_use]
    pub const fn is_put_if_different(self) -> bool {
        matches!(self, Self::GreaterOrEqual)
    }

    /// The version is replaced only by the `with_pinned` profile (`==`).
    #[must_use]
    pub const fn is_pinned_allowed_to_change(self) -> bool {
        matches!(self, Self::Equal)
    }
}

impl fmt::Display for Operator {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

/// One version constraint, like `>=1.2.3`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct VersionConstraint {
    /// The operator.
    pub operator: Operator,
    /// The version text as written (not parsed as PEP 440: it is written back verbatim).
    pub version: String,
}

impl VersionConstraint {
    /// A constraint with a validated version text.
    ///
    /// # Errors
    ///
    /// The message when the version is empty or does not start with a digit.
    pub fn new(operator: Operator, version: impl Into<String>) -> Result<Self, String> {
        let version = version.into();
        if version.trim().is_empty() {
            return Err("Version value cannot be empty or whitespace".to_owned());
        }
        if !version.chars().next().is_some_and(char::is_numeric) {
            return Err("Version value must start with a digit".to_owned());
        }
        Ok(Self { operator, version })
    }
}

impl fmt::Display for VersionConstraint {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}{}", self.operator, self.version)
    }
}

/// A parsed dependency string, like `requests[dev] >=1.2.3; python_version >= "3.10"`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DependencyParsed {
    /// The name as written (kept only with `--preserve-original-package-names`).
    pub original_name: Option<String>,
    /// The normalized name.
    pub package_name: PackageName,
    /// Extras, like `dev`.
    pub extras: Vec<String>,
    /// Version constraints in the written order.
    pub version_constraints: Vec<VersionConstraint>,
    /// The environment marker after `;`, as written.
    pub marker: Option<String>,
}

impl DependencyParsed {
    /// A dependency with only a name.
    #[must_use]
    pub fn new(package_name: PackageName) -> Self {
        Self {
            original_name: None,
            package_name,
            extras: Vec::new(),
            version_constraints: Vec::new(),
            marker: None,
        }
    }

    /// The name to write: the original spelling when kept, else the normalized one.
    #[must_use]
    pub fn get_name(&self) -> &str {
        self.original_name
            .as_deref()
            .unwrap_or_else(|| self.package_name.as_str())
    }

    /// `name[extra1,extra2]`.
    #[must_use]
    pub fn get_name_with_extras(&self) -> String {
        if self.extras.is_empty() {
            self.get_name().to_owned()
        } else {
            format!("{}[{}]", self.get_name(), self.extras.join(","))
        }
    }

    /// The constraints and the marker: `>=1,<2; marker`.
    #[must_use]
    pub fn get_partial_spec(&self) -> String {
        let mut out = String::new();
        if !self.version_constraints.is_empty() {
            let constraints: Vec<String> = self.version_constraints.iter().map(ToString::to_string).collect();
            out.push_str(&constraints.join(","));
        }
        if let Some(marker) = &self.marker {
            out.push_str("; ");
            out.push_str(marker);
        }
        out
    }

    /// The whole dependency string as this tool writes it.
    #[must_use]
    pub fn get_full_spec(&self) -> String {
        format!("{}{}", self.get_name_with_extras(), self.get_partial_spec())
    }
}

/// One accepted change of a dependency string.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ChangesItem {
    /// Before.
    pub from_item: DependencyParsed,
    /// After.
    pub to_item: DependencyParsed,
}

impl fmt::Display for ChangesItem {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{}: {} -> {}",
            self.from_item.get_name_with_extras(),
            self.from_item.get_partial_spec(),
            self.to_item.get_partial_spec()
        )
    }
}
