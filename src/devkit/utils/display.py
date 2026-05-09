"""Shared Rich display helpers and fzf integration."""

import subprocess

from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme

_theme = Theme(
    {
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "info": "bold cyan",
        "muted": "dim white",
    }
)

console = Console(theme=_theme)


# ── Panels ───────────────────────────────────────────────────────────────────

def success_panel(content: str, title: str = "OK") -> None:
    console.print(Panel(content, title=f"[success]{title}[/success]", border_style="green"))


def error_panel(content: str, title: str = "Error") -> None:
    console.print(Panel(content, title=f"[error]{title}[/error]", border_style="red"))


def ai_panel(content: str, title: str = "AI Response", tool: str = "gemini") -> None:
    colour = "cyan" if tool == "gemini" else "purple"
    console.print(
        Panel(content, title=f"[{colour}]{title}[/{colour}]", border_style=colour)
    )


# ── fzf ──────────────────────────────────────────────────────────────────────

def fzf_select(items: list[str], prompt: str = "Select > ") -> str:
    """Pipe items through fzf and return the selected line (empty string on cancel)."""
    proc = subprocess.run(
        ["fzf", f"--prompt={prompt}", "--height=40%", "--border", "--ansi"],
        input="\n".join(items),
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()
