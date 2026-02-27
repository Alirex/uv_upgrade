use std::str::FromStr;
use tokio::fs;
use toml_edit::DocumentMut;

pub type TomlContent = String;

pub type TomlDocumentMut = DocumentMut;

pub async fn toml_parse(content: &TomlContent) -> TomlDocumentMut {
    DocumentMut::from_str(content).unwrap()
}

pub async fn toml_load(path: &std::path::Path) -> Result<TomlDocumentMut, std::io::Error> {
    DocumentMut::from_str(&fs::read_to_string(path).await?).map_err(|e| {
        std::io::Error::new(
            std::io::ErrorKind::InvalidData,
            format!("Failed to parse TOML: {}", e),
        )
    })
}

pub async fn toml_dumps(data: &TomlDocumentMut) -> TomlContent {
    data.to_string()
}

pub async fn toml_save(path: &std::path::Path, data: &TomlDocumentMut) -> std::io::Result<()> {
    let text = toml_dumps(data).await;
    fs::write(path, text).await
}
