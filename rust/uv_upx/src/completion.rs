//! `--show-completion` and `--install-completion`, like Typer's: the shell is detected from `$SHELL`.

use std::path::{Path, PathBuf};

use clap::Command;
use clap_complete::Shell;

use crate::error::{Error, Result, read_text, write_text};

fn detect_shell() -> Result<Shell> {
    let shell = std::env::var("SHELL").unwrap_or_default();
    let name = PathBuf::from(&shell)
        .file_name()
        .map(|name| name.to_string_lossy().into_owned())
        .unwrap_or_default();
    match name.as_str() {
        "bash" => Ok(Shell::Bash),
        "zsh" => Ok(Shell::Zsh),
        "fish" => Ok(Shell::Fish),
        "pwsh" | "powershell" => Ok(Shell::PowerShell),
        "elvish" => Ok(Shell::Elvish),
        _ => Err(Error::Prompt(format!(
            "Shell {shell:?} is not supported for completion (bash, zsh, fish, powershell, elvish)."
        ))),
    }
}

fn script(command: &mut Command, shell: Shell) -> String {
    let name = command.get_name().to_owned();
    let mut buffer = Vec::new();
    clap_complete::generate(shell, command, name, &mut buffer);
    String::from_utf8_lossy(&buffer).into_owned()
}

/// Print the completion script of the current shell.
///
/// # Errors
///
/// When the shell is not recognized.
pub fn show_completion(command: &mut Command) -> Result<()> {
    let shell = detect_shell()?;
    print!("{}", script(command, shell));
    Ok(())
}

fn home() -> Result<PathBuf> {
    std::env::home_dir().ok_or_else(|| Error::Prompt("The home directory is unknown.".to_owned()))
}

fn append_once(rc_path: &Path, line: &str) -> Result<()> {
    let current = if rc_path.exists() {
        read_text(rc_path)?
    } else {
        String::new()
    };
    if current.contains(line) {
        return Ok(());
    }
    write_text(rc_path, &format!("{current}\n{line}\n"))
}

/// Install the completion of the current shell, where Typer puts it, and print where it went.
///
/// # Errors
///
/// When the shell is not recognized or a file cannot be written.
pub fn install_completion(command: &mut Command) -> Result<()> {
    let shell = detect_shell()?;
    let name = command.get_name().to_owned();
    let text = script(command, shell);
    let home = home()?;
    let path = match shell {
        Shell::Bash => {
            let path = home.join(".bash_completions").join(format!("{name}.sh"));
            write_in_dir(&path, &text)?;
            append_once(&home.join(".bashrc"), &format!("source {}", path.display()))?;
            path
        }
        Shell::Zsh => {
            let path = home.join(".zfunc").join(format!("_{name}"));
            write_in_dir(&path, &text)?;
            append_once(&home.join(".zshrc"), "fpath+=~/.zfunc\nautoload -Uz compinit\ncompinit")?;
            path
        }
        Shell::Fish => {
            let path = home.join(".config/fish/completions").join(format!("{name}.fish"));
            write_in_dir(&path, &text)?;
            path
        }
        _ => {
            return Err(Error::Prompt(format!(
                "Automatic installation is not supported for {shell}; use --show-completion and add the script to \
                 your profile."
            )));
        }
    };
    println!("{shell} completion installed in {}", path.display());
    println!("Completion will take effect once you restart the terminal");
    Ok(())
}

fn write_in_dir(path: &Path, text: &str) -> Result<()> {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).map_err(|source| Error::Io {
            action: "Failed to create",
            path: parent.to_path_buf(),
            source,
        })?;
    }
    write_text(path, text)
}
