"""
devkit ai — AI CLI integrations
Phase 3: explain, suggest, review, commit, ask
Tool used: gemini (Copilot CLI deprecated Oct 2025)
"""

from __future__ import annotations

import subprocess

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt

from devkit.utils.check import check_tools, tool_available
from devkit.utils.display import ai_panel, console, error_panel
from devkit.utils.gh import GhError, gh, gh_json

app = typer.Typer(help="AI tools — Gemini CLI")

TOOL = "gemini"


# ── internal helper ───────────────────────────────────────────────────────────

def _run_gemini(prompt: str) -> str:
    """Call `gemini -p <prompt>` and return stdout."""
    if not tool_available("gemini"):
        error_panel(
            "gemini CLI not found.\n"
            "Install: npm install -g @google/gemini-cli\n"
            "Auth:    Set GEMINI_API_KEY in ~/.gemini/.env",
            "gemini not found",
        )
        raise typer.Exit(1)
    result = subprocess.run(
        ["gemini", "-p", prompt],
        capture_output=True,
        text=True,
    )
    out = result.stdout.strip()
    return out or result.stderr.strip() or "(no output)"


# ── commands ──────────────────────────────────────────────────────────────────

@app.command()
def explain(
    command: str = typer.Argument(..., help="Shell command to explain"),
):
    """Ask Gemini to explain a shell command in plain English."""
    prompt = (
        f"Explain what this shell command does, step by step:\n\n{command}\n\n"
        "Be concise and practical. Mention any risks or common use cases."
    )
    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  console=console) as p:
        p.add_task("Asking Gemini…")
        output = _run_gemini(prompt)
    ai_panel(output, title=f"Gemini — explain: {command}", tool=TOOL)


@app.command()
def suggest(
    task: str = typer.Argument(..., help="Task to accomplish in natural language"),
    target: str = typer.Option("shell", help="Target type: shell | git | gh"),
):
    """Ask Gemini to suggest a command for a given task."""
    target_hints = {
        "shell": "a Unix/Linux shell command (bash/zsh)",
        "git":   "a git command",
        "gh":    "a GitHub CLI (gh) command",
    }
    hint = target_hints.get(target, "a shell command")
    prompt = (
        f"Suggest {hint} to accomplish this task:\n\n{task}\n\n"
        "Reply with ONLY the command, then a one-line explanation below it. "
        "No markdown fences."
    )
    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  console=console) as p:
        p.add_task("Asking Gemini…")
        output = _run_gemini(prompt)
    ai_panel(output, title=f"Gemini — suggest ({target}): {task}", tool=TOOL)


@app.command()
def review(
    pr_number: int = typer.Argument(..., help="PR number to review"),
    repo: str = typer.Option("", help="owner/repo (default: current repo)"),
):
    """AI-powered code review of a pull request using Gemini."""
    check_tools(["gh"])
    repo_args = ["--repo", repo] if repo else []

    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  console=console) as progress:
        t = progress.add_task("Fetching PR diff…")
        try:
            diff = gh("pr", "diff", str(pr_number), *repo_args)
            info = gh_json(
                "pr", "view", str(pr_number),
                "--json", "title,body",
                *repo_args,
            )
        except GhError as exc:
            error_panel(str(exc), "gh error")
            raise typer.Exit(1)

        pr_title = info.get("title", f"PR #{pr_number}")
        prompt = (
            f'Review this pull request titled "{pr_title}".\n'
            "Focus on: correctness, edge cases, readability, and potential bugs.\n"
            "Be concise and actionable.\n\n"
            f"--- DIFF (truncated to 4000 chars) ---\n{diff[:4000]}"
        )

        progress.update(t, description="Running Gemini review…")
        output = _run_gemini(prompt)

    ai_panel(output, title=f"Gemini Review — PR #{pr_number}", tool=TOOL)


@app.command()
def commit():
    """Generate a conventional commit message from staged changes using Gemini."""
    check_tools(["git"])

    diff = subprocess.check_output(["git", "diff", "--staged"], text=True)
    if not diff.strip():
        console.print("[warning]No staged changes found. Use `git add` first.[/warning]")
        raise typer.Exit()

    prompt = (
        "Write a conventional commit message for these staged changes.\n"
        "Format: <type>(<scope>): <short description>\n"
        "Then add a blank line and 2–3 bullet points explaining what changed.\n"
        "Reply with ONLY the commit message, no extra commentary.\n\n"
        f"--- DIFF ---\n{diff[:3000]}"
    )

    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  console=console) as p:
        p.add_task("Generating commit message with Gemini…")
        suggested = _run_gemini(prompt)

    ai_panel(suggested, title="Suggested Commit Message", tool=TOOL)

    use_it = Confirm.ask("Use this commit message?")
    if use_it:
        subprocess.run(["git", "commit", "-m", suggested], check=True)
        console.print("[success]✓[/success] Committed!")
    else:
        manual = Prompt.ask("Enter your own message")
        subprocess.run(["git", "commit", "-m", manual], check=True)
        console.print("[success]✓[/success] Committed!")


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question or task for Gemini"),
):
    """Ask Gemini a free-form question."""
    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  console=console) as p:
        p.add_task("Asking Gemini…")
        output = _run_gemini(question)
    ai_panel(output, title=f"Gemini — {question[:50]}", tool=TOOL)
