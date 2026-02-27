mod functions;

mod change_content_of_line;

pub use change_content_of_line::change_value_from_toml_array;
pub use functions::{TomlDocumentMut, toml_dumps, toml_load, toml_parse, toml_save};
