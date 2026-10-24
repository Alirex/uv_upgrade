//! `file://` URIs of paths, as Python's `pathlib.Path.as_uri()` prints them.

use std::fmt::Write;
use std::path::Path;

/// Percent-encode everything except the unreserved characters and `/` (what `pathlib` keeps).
fn quote(bytes: &[u8], out: &mut String) {
    for &byte in bytes {
        if byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'.' | b'_' | b'~' | b'/') {
            out.push(char::from(byte));
        } else {
            // Writing to a String cannot fail.
            let _ = write!(out, "%{byte:02X}");
        }
    }
}

/// The `file://` URI of an absolute path, like `pathlib.Path.as_uri()`.
///
/// A relative path is made absolute against the current directory first (Python raises `ValueError` there).
#[must_use]
pub fn path_as_uri(path: &Path) -> String {
    let absolute = if path.is_absolute() {
        path.to_path_buf()
    } else {
        std::env::current_dir().map_or_else(|_| path.to_path_buf(), |cwd| cwd.join(path))
    };
    let mut out = String::from("file://");
    #[cfg(unix)]
    {
        use std::os::unix::ffi::OsStrExt;
        quote(absolute.as_os_str().as_bytes(), &mut out);
    }
    #[cfg(not(unix))]
    {
        let text = absolute.to_string_lossy().replace('\\', "/");
        // `C:/x` becomes `file:///C:/x`.
        if !text.starts_with('/') {
            out.push('/');
        }
        quote(text.as_bytes(), &mut out);
    }
    out
}

#[cfg(test)]
mod tests {
    use std::path::Path;

    use super::path_as_uri;

    #[test]
    fn encodes_like_pathlib() {
        assert_eq!(
            path_as_uri(Path::new("/tmp/a b/ü#?%+@:,")),
            "file:///tmp/a%20b/%C3%BC%23%3F%25%2B%40%3A%2C"
        );
        assert_eq!(
            path_as_uri(Path::new("/tmp/x~y.z-_(1)[2]!*'&=$;")),
            "file:///tmp/x~y.z-_%281%29%5B2%5D%21%2A%27%26%3D%24%3B"
        );
    }
}
