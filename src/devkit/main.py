"""
devkit — AI-powered developer CLI toolkit
Entry point: registers all command groups and global options.
"""

from __future__ import annotations

import typer
from rich.panel import Panel
from rich.table import Table

from devkit import config
from devkit.commands import ai, github, workflow
from devkit.utils.check import check_tools, warn_optional
from devkit.utils.display import console

app = typer.Typer(
    name="devkit",
    help="[bold cyan]devkit[/bold cyan] — AI-powered developer toolkit (gh · Gemini)",
    rich_markup_mode="rich",
    no_args_is_help=False,
)

# Register sub-apps
app.add_typer(github.app, name="gh", help="GitHub operations (issues, PRs, branches…)")
app.add_typer(ai.app, name="ai", help="AI tools — Gemini CLI")
app.add_typer(workflow.app, name="workflow", help="End-to-end developer workflows")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Show welcome screen when invoked without a sub-command."""
    if ctx.invoked_subcommand is None:
        _show_welcome()


def _show_welcome() -> None:
    console.print(
        Panel(
            "[bold cyan]devkit[/bold cyan]  v0.1.0\n"
            "[dim]AI-powered developer toolkit — gh · Gemini[/dim]",
            border_style="cyan",
            expand=False,
        )
    )

    table = Table(show_header=True, header_style="bold", border_style="dim")
    table.add_column("Command group", style="cyan", width=18)
    table.add_column("Commands")

    table.add_row(
        "devkit gh",
        "issues · pr-summary · start-feature · open-pr · run-status",
    )
    table.add_row(
        "devkit ai",
        "explain · suggest · review · commit · ask",
    )
    table.add_row(
        "devkit workflow",
        "feature-start · pr-ship · daily-standup",
    )
    table.add_row(
        "devkit config",
        "show · set",
    )

    console.print(table)
    console.print("\nRun [cyan]devkit <command> --help[/cyan] for details.\n")


# ── config sub-app ────────────────────────────────────────────────────────────

cfg_app = typer.Typer(help="Manage devkit configuration (~/.devkit/config.json)")
app.add_typer(cfg_app, name="config")


@cfg_app.command("show")
def config_show() -> None:
    """Show current devkit configuration."""
    cfg = config.load_config()
    table = Table(title="devkit config", border_style="cyan")
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    for k, v in cfg.items():
        table.add_row(k, str(v))
    console.print(table)
    console.print(f"[dim]Config file: {config.CONFIG_FILE}[/dim]")


@cfg_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Config key (e.g. ai_tool)"),
    value: str = typer.Argument(..., help="New value"),
) -> None:
    """Set a configuration value."""
    cfg = config.load_config()
    if key not in config.DEFAULTS:
        console.print(f"[error]Unknown config key '{key}'.[/error]")
        console.print(f"Valid keys: {', '.join(config.DEFAULTS)}")
        raise typer.Exit(1)
    cfg[key] = value
    config.save_config(cfg)
    console.print(f"[success]✓[/success] {key} = {value}")


if __name__ == "__main__":
    app()
