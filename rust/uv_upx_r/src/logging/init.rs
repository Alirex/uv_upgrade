// use tracing_subscriber::FmtSubscriber;
//
// pub fn init_logging() {
//     let subscriber = FmtSubscriber::builder()
//         .with_max_level(tracing::Level::INFO)
//         .with_target(false)
//         .finish();
//     tracing::subscriber::set_global_default(subscriber).expect("setting default subscriber failed");
// }

use tracing_appender::non_blocking::WorkerGuard;
use tracing_subscriber::{Layer, Registry, filter, fmt, layer::SubscriberExt};

// const LOG_FILE_NAME_PREFIX: &str = "app_name";
// const LOG_FILE_NAME_SUFFIX: &str = "log";

pub fn init_logging() -> Vec<WorkerGuard> {
    // let logs_dir = get_logs_dir();
    // std::fs::create_dir_all(&logs_dir).expect("Failed to create logs directory");
    //
    // const AMOUNT_OF_LOG_FILES: usize = 3;
    //
    // // let file_appender = tracing_appender::rolling::daily(logs_dir, LOG_FILE_NAME);
    // let file_appender = RollingFileAppender::builder()
    //     .rotation(Rotation::DAILY)
    //     .filename_prefix(LOG_FILE_NAME_PREFIX)
    //     .filename_suffix(LOG_FILE_NAME_SUFFIX)
    //     .max_log_files(AMOUNT_OF_LOG_FILES)
    //     .build(&logs_dir)
    //     .expect("Failed to create file appender");
    //
    // let (file_writer, _guard_file) = tracing_appender::non_blocking(file_appender);

    let (stdout_writer, _guard_stdout) = tracing_appender::non_blocking(std::io::stdout());

    // let file_layer = fmt::layer()
    //     .with_writer(file_writer)
    //     .with_ansi(false)
    //     .with_target(false)
    //     .with_file(true)
    //     .with_line_number(true)
    //     .with_level(true)
    //     .with_filter(filter::LevelFilter::from(tracing::Level::INFO));

    let stdout_layer = fmt::layer()
        .with_writer(stdout_writer)
        .with_ansi(true)
        .with_target(false)
        .with_file(false)
        .with_line_number(false)
        .with_level(true)
        .with_filter(filter::LevelFilter::from(tracing::Level::INFO));

    // TODO: Add .with_max_level(tracing::Level::INFO)

    // let subscriber = Registry::default().with(file_layer).with(stdout_layer);
    let subscriber = Registry::default().with(stdout_layer);

    tracing::subscriber::set_global_default(subscriber).expect("setting default subscriber failed");

    vec![
        //
        // _guard_file,
        _guard_stdout,
    ]
}
