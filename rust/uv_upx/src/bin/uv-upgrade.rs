//! The short CLI: `uv-upgrade` is `uv-upx upgrade run`.

use std::process::ExitCode;

fn main() -> ExitCode {
    uv_upx::cli::main_short(std::env::args_os())
}
