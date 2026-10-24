//! Log lines on stderr in the format of the Python package (`logging.basicConfig` with
//! `%(asctime)s - %(name)s - %(levelname)s - %(message)s`), so the two implementations print the same lines.

use std::fmt::Display;

/// Write one log line to stderr.
fn log(level: &str, name: &str, message: &dyn Display) {
    let now = chrono::Local::now().format("%Y-%m-%d %H:%M:%S,%3f");
    eprintln!("{now} - {name} - {level} - {message}");
}

/// An `INFO` line of the logger `name` (a Python module path, like the original).
pub fn info(name: &str, message: &dyn Display) {
    log("INFO", name, message);
}

/// A `WARNING` line.
pub fn warning(name: &str, message: &dyn Display) {
    log("WARNING", name, message);
}

/// An `ERROR` line.
pub fn error(name: &str, message: &dyn Display) {
    log("ERROR", name, message);
}
