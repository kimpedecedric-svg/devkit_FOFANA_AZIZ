"""
devkit ai — AI CLI integrations
Phase 3: explain (Copilot), suggest (Copilot), review (Gemini), commit (Gemini)
Tools used: gh copilot, gemini
"""

from __future__ import annotations

import subprocess

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt

from devkit import config
from devkit.utils.check import check_tools, tool_available
from devkit.utils.display import ai_panel, console, error_panel
from devkit.utils.gh import GhError, gh, gh_json

app = typer.Typer(help="AI tools — Copilot CLI & Gemini CLI")


# ── internal helpers ──────────────────────────────────────────────────────────

def _run_gemini(prompt: str) -> str:
    """Call the gemini CLI with a text prompt, return its stdout."""
    result = subprocess.run(
        ["gemini", prompt],
        capture_output=True,
        text=True,
    )
    out = result.stdout.strip()
    return out or result.stderr.strip() or "(no output)"


def _run_copilot(subcommand: str, text: str, target: str = "") -> str:
    """Call `gh copilot suggest|explain <text>` and return stdout."""
    cmd = ["gh", "copilot", subcommand]
    if target:
        cmd += ["--target", target]
    cmd.append(text)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip() or result.stderr.strip() or "(no output)"


def _ai_tool() -> str:
    """Return user's preferred AI tool from config."""
    return config.get("ai_tool") or "gemini"


# ── commands ──────────────────────────────────────────────────────────────────

@app.command()
def explain(
    command: str = typer.Argument(..., help="Shell command to explain"),
):
    """Ask Copilot CLI to explain a shell command."""
    check_tools(["gh"])
    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  console=console) as p:
        p.add_task("Asking Copilot…")
        output = _run_copilot("explain", command)
    ai_panel(output, title=f"Copilot — explain: {command}", tool="copilot")


@app.command()
def suggest(
    task: str = typer.Argument(..., help="Task to accomplish in natural language"),
    target: str = typer.Option("shell", help="Target: shell | git | gh"),
):
    """Ask Copilot CLI to suggest a shell command."""
    check_tools(["gh"])
    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  console=console) as p:
        p.add_task("Asking Copilot…")
        output = _run_copilot("suggest", task, target=target)
    ai_panel(output, title=f"Copilot — suggest ({target}): {task}", tool="copilot")


@app.command()
def review(
    pr_number: int = typer.Argument(..., help="PR number to review"),
    repo: str = typer.Option("", help="owner/repo (default: current repo)"),
    tool: str = typer.Option("", help="AI tool to use: gemini | copilot (overrides config)"),
):
    """AI-powered code review of a pull request (uses Gemini or Copilot)."""
    check_tools(["gh"])
    ai = tool or _ai_tool()

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
            f"Focus on: correctness, edge cases, readability, and any bugs.\n\n"
            f"--- DIFF (truncated to 4000 chars) ---\n{diff[:4000]}"
        )

        progress.update(t, description=f"Running AI review with {ai}…")

        if ai == "gemini":
            if not tool_available("gemini"):
                error_panel("gemini CLI not found. Install: npm install -g @google/generative-ai-cli")
                raise typer.Exit(1)
            output = _run_gemini(prompt)
        else:
            # Fallback to Copilot explain on the diff summary
            output = _run_copilot("explain", prompt[:500])

    ai_panel(output, title=f"AI Review — PR #{pr_number} ({ai})", tool=ai)


@app.command()
def commit(
    tool: str = typer.Option("", help="AI tool: gemini | copilot (overrides config)"),
):
    """Generate a conventional commit message from staged changes."""
    check_tools(["git"])
    ai = tool or _ai_tool()

    diff = subprocess.check_output(["git", "diff", "--staged"], text=True)
    if not diff.strip():
        console.print("[warning]No staged changes found. Use `git add` first.[/warning]")
        raise typer.Exit()

    prompt = (
        "Write a conventional commit message for these staged changes.\n"
        "Format: <type>(<scope>): <short description>\n"
        "Then add a blank line and 2–3 bullet points explaining what changed.\n\n"
        f"--- DIFF ---\n{diff[:3000]}"
    )

    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  console=console) as p:
        p.add_task(f"Generating commit message with {ai}…")

        if ai == "gemini":
            if not tool_available("gemini"):
                error_panel("gemini CLI not found.")
                raise typer.Exit(1)
            suggested = _run_gemini(prompt)
        else:
            suggested = _run_copilot("suggest", prompt[:400], target="git")

    ai_panel(suggested, title="Suggested Commit Message", tool=ai)

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
    question: str = typer.Argument(..., help="Question or task for the AI"),
    tool: str = typer.Option("", help="AI tool: gemini | copilot"),
):
    """Ask Gemini or Copilot a free-form question."""
    ai = tool or _ai_tool()

    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  console=console) as p:
        p.add_task(f"Asking {ai}…")

        if ai == "gemini":
            if not tool_available("gemini"):
                error_panel("gemini CLI not found.")
                raise typer.Exit(1)
            output = _run_gemini(question)
        else:
            check_tools(["gh"])
            output = _run_copilot("suggest", question)

    ai_panel(output, title=f"{ai} — {question[:50]}", tool=ai)
