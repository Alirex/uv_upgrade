use clap_markdown::MarkdownOptions;
use path_as_uri::get_path_as_uri_string;
use std::path::Path;

pub async fn write_help_as_markdown<T>(path_to_write: &Path)
where
    T: clap::CommandFactory + clap::Parser,
{
    let path_to_write = path_to_write.canonicalize().unwrap();

    let options = MarkdownOptions::default()
        .show_table_of_contents(true)
        .show_footer(false);

    let content = clap_markdown::help_markdown_custom::<T>(&options);

    match tokio::fs::write(&path_to_write, content).await {
        Ok(_) => {}
        Err(e) => panic!("Cannot write help to: {path_to_write:?}: {e}"),
    }

    println!(
        "Help written to: {path_to_write}",
        path_to_write = get_path_as_uri_string(&path_to_write)
    );
}
