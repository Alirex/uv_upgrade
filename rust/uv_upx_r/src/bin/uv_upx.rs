use uv_upx_r::cli::cli_runner::cli_runner;

#[tokio::main]
async fn main() {
    cli_runner().await;
}
