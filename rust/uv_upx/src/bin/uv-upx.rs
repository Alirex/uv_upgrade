//! The full CLI: `uv-upx upgrade run`, `uv-upx helpers ...`.

use std::process::ExitCode;

fn main() -> ExitCode {
    uv_upx::cli::main_full(std::env::args_os())
}
