//! Typed access to the nodes of a `toml_edit` document (the counterpart of `services/toml/typed_access.py`).

use std::path::Path;

use toml_edit::{Array, DocumentMut, Item, Value};

use crate::error::{Error, Result};

/// Parse a TOML text, with the file path in the error.
///
/// # Errors
///
/// `Error::Toml` when the text does not parse.
pub fn toml_parse(text: &str, path: &Path) -> Result<DocumentMut> {
    text.parse::<DocumentMut>().map_err(|source| Error::Toml {
        path: path.to_path_buf(),
        source,
    })
}

/// Whether the item is a table (a standard, inline or dotted one).
#[must_use]
pub fn is_table(item: Option<&Item>) -> bool {
    item.is_some_and(|item| item.as_table_like().is_some())
}

/// Walk down the tables of a document by keys. `None` when a key is missing or a parent is not a table.
#[must_use]
pub fn get_node<'a>(doc: &'a DocumentMut, path: &[&str]) -> Option<&'a Item> {
    let mut node = doc.as_item();
    for key in path {
        node = node.as_table_like()?.get(key)?;
    }
    Some(node)
}

/// The mutable node at the path (see [`get_node`]).
#[must_use]
pub fn get_node_mut<'a>(doc: &'a mut DocumentMut, path: &[&str]) -> Option<&'a mut Item> {
    let mut node = doc.as_item_mut();
    for key in path {
        node = node.as_table_like_mut()?.get_mut(key)?;
    }
    Some(node)
}

/// The names of the arrays that are direct values of the table at the path, in file order. Other values are skipped.
#[must_use]
pub fn get_array_names_in_table(doc: &DocumentMut, path: &[&str]) -> Vec<String> {
    let Some(table) = get_node(doc, path).and_then(Item::as_table_like) else {
        return Vec::new();
    };
    table
        .iter()
        .filter(|(_, value)| value.as_array().is_some())
        .map(|(key, _)| key.to_owned())
        .collect()
}

/// The string items of an array, with their value index; non-string items (like `{ include-group = "x" }`) are
/// returned as `None` at their index.
#[must_use]
pub fn array_strings(array: &Array) -> Vec<Option<&str>> {
    array.iter().map(Value::as_str).collect()
}

/// Replace the string at `index` of an array, keeping its surrounding whitespace and comments.
pub fn set_array_string(array: &mut Array, index: usize, text: &str) {
    let Some(old) = array.get(index) else {
        return;
    };
    let decor = old.decor().clone();
    let mut new = Value::from(text);
    *new.decor_mut() = decor;
    array.replace(index, new);
}

#[cfg(test)]
mod tests {
    #![expect(clippy::unwrap_used, reason = "a test panics on an unexpected value")]

    use std::path::Path;

    use super::{
        array_strings, get_array_names_in_table, get_node, get_node_mut, is_table, set_array_string, toml_parse,
    };

    const PYPROJECT: &str = r#"
[project]
name = "foo"
dependencies = [
    "httpx>=0.24.0",  # comment
    { include-group = "dev" },
]

[tool.ruff]
line-length = 120

[project.optional-dependencies]
cli = ["typer"]
not-an-array = "text"

[dependency-groups]
dev = ["pytest"]
"#;

    fn doc() -> toml_edit::DocumentMut {
        toml_parse(PYPROJECT, Path::new("pyproject.toml")).unwrap()
    }

    #[test]
    fn get_node_returns_live_nodes() {
        let mut data = doc();
        let node = get_node_mut(&mut data, &["dependency-groups", "dev"]).unwrap();
        let array = node.as_array_mut().unwrap();
        set_array_string(array, 0, "pytest>=9");
        assert!(data.to_string().contains(r#"dev = ["pytest>=9"]"#));
    }

    #[test]
    fn get_node_missing_path() {
        let data = doc();
        assert!(get_node(&data, &["missing"]).is_none());
        assert!(get_node(&data, &["project", "name", "deeper"]).is_none());
        assert!(get_node(&data, &[]).is_some_and(|item| item.as_table_like().is_some()));
    }

    #[test]
    fn get_node_through_out_of_order_table() {
        let data = doc();
        let node = get_node(&data, &["project", "optional-dependencies", "cli"]).unwrap();
        assert_eq!(array_strings(node.as_array().unwrap()), vec![Some("typer")]);
    }

    #[test]
    fn is_table_cases() {
        let data = doc();
        assert!(is_table(get_node(&data, &[])));
        assert!(is_table(get_node(&data, &["project"])));
        assert!(!is_table(get_node(&data, &["project", "name"])));
        assert!(!is_table(None));
    }

    #[test]
    fn get_arrays_in_table_skips_not_arrays() {
        let data = doc();
        assert_eq!(
            get_array_names_in_table(&data, &["project", "optional-dependencies"]),
            vec!["cli"]
        );
        assert_eq!(get_array_names_in_table(&data, &["missing"]), Vec::<String>::new());
        assert_eq!(
            get_array_names_in_table(&data, &["project", "name"]),
            Vec::<String>::new()
        );
    }

    #[test]
    fn array_items_keeps_order_and_non_strings() {
        let data = doc();
        let array = get_node(&data, &["project", "dependencies"])
            .unwrap()
            .as_array()
            .unwrap();
        assert_eq!(array_strings(array), vec![Some("httpx>=0.24.0"), None]);
    }

    #[test]
    fn set_array_string_keeps_decor_and_requotes() {
        let source = "deps = [\n    'a',  # c\n        \"b\" ,\n]\n";
        let mut data = toml_parse(source, Path::new("x")).unwrap();
        let array = get_node_mut(&mut data, &["deps"]).unwrap().as_array_mut().unwrap();
        set_array_string(array, 0, "a>=1");
        set_array_string(array, 1, "b>=2");
        assert_eq!(
            data.to_string(),
            "deps = [\n    \"a>=1\",  # c\n        \"b>=2\" ,\n]\n"
        );
    }
}
