"""Check that required external tools are installed."""

import shutil
from rich.console import Console

console = Console(stderr=True)

REQUIRED_TOOLS: dict[str, str] = {
    "gh": "Install from https://cli.github.com",
    "fzf": "brew install fzf  |  apt install fzf",
    "bat": "brew install bat  |  apt install bat",
    "delta": "brew install git-delta",
    "git": "Install from https://git-scm.com",
}

OPTIONAL_TOOLS: dict[str, str] = {
    "gemini": "npm install -g @google/generative-ai-cli",
    "asciinema": "brew install asciinema  |  pip install asciinema",
}


def check_tools(require: list[str] | None = None) -> None:
    """
    Check a subset (or all) required tools.
    Raises SystemExit(1) if any are missing.
    """
    tools = {k: v for k, v in REQUIRED_TOOLS.items()
             if require is None or k in require}
    missing = {t: hint for t, hint in tools.items() if not shutil.which(t)}
    if missing:
        console.print("\n[bold red]✗ Missing required tools:[/bold red]")
        for tool, hint in missing.items():
            console.print(f"  [cyan]{tool:<12}[/cyan] → {hint}")
        console.print()
        raise SystemExit(1)


def warn_optional() -> None:
    """Print warnings for missing optional tools (no exit)."""
    for tool, hint in OPTIONAL_TOOLS.items():
        if not shutil.which(tool):
            console.print(
                f"[yellow]⚠  Optional tool [bold]{tool}[/bold] not found — {hint}[/yellow]"
            )


def tool_available(name: str) -> bool:
    return shutil.which(name) is not None
