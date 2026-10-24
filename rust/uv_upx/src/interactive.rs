//! The interactive mode: accept or reject each proposed change.

use std::io::IsTerminal;
use std::path::Path;

use crate::collect::DependencyGroup;
use crate::dependency::ChangesItem;
use crate::error::{Error, Result};
use crate::path_uri::path_as_uri;

const RULE: &str = "========================================";

/// Print the introduction of the interactive mode.
pub fn show_interactive_information() {
    println!(
        "You are running in interactive mode.\n\
         You will be prompted for each proposed change.\n\
         \n\
         Note: These changes related to updating dependencies in pyproject.toml files.\n\
         It is implying how dependencies will be updated.\n\
         But, if you reject \">=X.Y.Z\" change, it will not updated in pyproject.toml,\n\
         but it may still be updated in the lock file (e.g., uv.lock).\n"
    );
}

/// Wrap in an ANSI style when stdout is a terminal.
fn styled(code: &str, text: &str) -> String {
    if std::io::stdout().is_terminal() {
        format!("\x1b[{code}m{text}\x1b[0m")
    } else {
        text.to_owned()
    }
}

/// Ask the user whether to apply one change.
///
/// # Errors
///
/// `Error::Prompt` when the prompt cannot run or is interrupted (Ctrl-C).
pub fn ask_interactive_confirmation(changes_item: &ChangesItem, group: &DependencyGroup, path: &Path) -> Result<bool> {
    println!("{RULE}");
    println!("In file: {}", path_as_uri(path));
    let folder_name = path
        .parent()
        .and_then(Path::file_name)
        .map(|name| name.to_string_lossy().into_owned())
        .unwrap_or_default();
    println!("Parent folder: {}", styled("1", &folder_name));
    println!("Group: {}", styled("1", &group.title()));

    let message = format!(
        "{} {} {} {}",
        styled("1;34", &format!("{}:", changes_item.from_item.get_name_with_extras())),
        styled("31", &changes_item.from_item.get_partial_spec()),
        styled("33", "\u{2192}"),
        styled("32", &changes_item.to_item.get_partial_spec()),
    );

    let answer = inquire::Select::new(&message, vec!["Accept", "Reject"])
        .without_filtering()
        .without_help_message()
        .prompt()
        .map_err(|error| Error::Prompt(error.to_string()))?;

    println!("{RULE}");
    Ok(answer == "Accept")
}
