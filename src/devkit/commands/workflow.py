"""
devkit workflow — End-to-end developer workflows
Phase 4: feature-start, pr-ship, daily-standup
Chains gh + git + Gemini into cohesive multi-step actions.
"""

from __future__ import annotations

import subprocess

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm

from devkit import config
from devkit.utils.check import check_tools, tool_available
from devkit.utils.display import ai_panel, console, error_panel
from devkit.utils.gh import GhError, gh, gh_json

app = typer.Typer(help="End-to-end developer workflows")


def _gemini(prompt: str) -> str:
    import subprocess as sp
    r = sp.run(["gemini", "-p", prompt], capture_output=True, text=True)
    return r.stdout.strip() or r.stderr.strip() or "(no output)"


# ── feature-start ─────────────────────────────────────────────────────────────

@app.command(name="feature-start")
def feature_start(
    name: str = typer.Argument(..., help="Feature name in kebab-case"),
    issue: int = typer.Option(None, "--issue", "-i", help="GitHub issue number to link"),
    no_ai: bool = typer.Option(False, "--no-ai", help="Skip AI scaffolding step"),
):
    """
    Full feature kickoff: branch → push → draft PR → AI implementation plan.

    Chains: git + gh + Gemini (or Copilot)
    """
    check_tools(["gh", "git"])
    ai_tool = config.get("ai_tool") or "gemini"

    console.rule("[bold cyan]🚀 Starting Feature[/bold cyan]")

    # 1. Create branch
    branch = f"feature/{name}"
    try:
        subprocess.run(["git", "checkout", "-b", branch], check=True)
    except subprocess.CalledProcessError:
        error_panel(f"Could not create branch '{branch}'. Does it already exist?")
        raise typer.Exit(1)
    console.print(f"[success]✓[/success] Branch created: [cyan]{branch}[/cyan]")

    # 2. Push branch
    try:
        subprocess.run(["git", "push", "-u", "origin", branch], check=True)
        console.print(f"[success]✓[/success] Pushed to origin")
    except subprocess.CalledProcessError:
        console.print("[warning]⚠  Could not push branch (no remote?)[/warning]")

    # 3. Commit vide pour permettre la création de la PR (GitHub l'exige)
    try:
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", f"chore: init feature/{name}"],
            check=True, capture_output=True,
        )
        subprocess.run(["git", "push"], check=True, capture_output=True)
        console.print(f"[success]\u2713[/success] Initial commit pushed")
    except subprocess.CalledProcessError:
        pass  # non bloquant

    # 4. Create draft PR
    pr_title = name.replace("-", " ").title()
    pr_body = f"Closes #{issue}" if issue else ""
    try:
        pr_url = gh("pr", "create", "--draft", "--title", pr_title, "--body", pr_body)
        console.print(f"[success]✓[/success] Draft PR: {pr_url}")
    except GhError as exc:
        console.print(f"[warning]⚠  Could not create PR: {exc}[/warning]")

    # 4. AI scaffold
    if not no_ai:
        issue_context = ""
        if issue:
            try:
                info = gh_json("issue", "view", str(issue), "--json", "title,body")
                issue_context = (
                    f"\nIssue #{issue}: {info.get('title', '')}\n{info.get('body', '')}"
                )
            except GhError:
                pass

        prompt = (
            f"I'm starting work on a feature called '{name}'.{issue_context}\n\n"
            "Give me a concise step-by-step implementation plan with:\n"
            "- Key files to create or modify\n"
            "- Main functions/classes to implement\n"
            "- Potential edge cases to watch out for\n"
            "Keep it practical and under 300 words."
        )

        with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                      console=console) as p:
            p.add_task(f"Generating AI plan with {ai_tool}…")
            if tool_available("gemini"):
                plan = _gemini(prompt)
            else:
                plan = "(gemini not available — install: npm install -g @google/gemini-cli)"

        ai_panel(plan, title="AI Implementation Plan", tool=ai_tool)

    console.rule("[bold green]✓ Ready to code![/bold green]")


# ── pr-ship ───────────────────────────────────────────────────────────────────

@app.command(name="pr-ship")
def pr_ship(
    pr_number: int = typer.Argument(..., help="PR number to review and merge"),
    repo: str = typer.Option("", help="owner/repo"),
):
    """
    Full PR ship pipeline: AI review → confirm → merge.

    Chains: gh pr diff → Gemini review → gh pr merge
    """
    check_tools(["gh"])
    ai_tool = config.get("ai_tool") or "gemini"
    repo_args = ["--repo", repo] if repo else []

    console.rule(f"[bold cyan]🚢 Shipping PR #{pr_number}[/bold cyan]")

    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  console=console) as p:
        t = p.add_task("Fetching PR diff…")
        try:
            diff = gh("pr", "diff", str(pr_number), *repo_args)
            info = gh_json("pr", "view", str(pr_number),
                           "--json", "title,state,reviews",
                           *repo_args)
        except GhError as exc:
            error_panel(str(exc))
            raise typer.Exit(1)

        p.update(t, description=f"Reviewing with {ai_tool}…")
        prompt = (
            f"Quick sanity check for PR '{info.get('title', pr_number)}'.\n"
            f"Is this diff safe to merge? Note any red flags.\n\n{diff[:3000]}"
        )

        if ai_tool == "gemini" and tool_available("gemini"):
            review = _gemini(prompt)
        else:
            review = "(AI review skipped — gemini not available)"

    ai_panel(review, title=f"AI Review — PR #{pr_number}", tool=ai_tool)

    if Confirm.ask("Merge this PR?"):
        try:
            gh("pr", "merge", str(pr_number), "--squash", "--auto", *repo_args)
            console.print(f"[success]✓[/success] PR #{pr_number} merged!")
        except GhError as exc:
            error_panel(str(exc))
    else:
        console.print("[muted]Merge cancelled.[/muted]")


# ── daily-standup ─────────────────────────────────────────────────────────────

@app.command(name="daily-standup")
def daily_standup(
    repo: str = typer.Option("", help="owner/repo"),
    days: int = typer.Option(1, help="Look back N days"),
):
    """
    Generate a daily standup summary from recent PRs and issues.

    Chains: gh pr list + gh issue list → Gemini summary
    """
    check_tools(["gh"])
    ai_tool = config.get("ai_tool") or "gemini"
    repo_args = ["--repo", repo] if repo else []

    console.rule("[bold cyan]📋 Daily Standup[/bold cyan]")

    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  console=console) as p:
        p.add_task("Fetching recent activity…")
        try:
            prs = gh_json(
                "pr", "list",
                "--json", "number,title,state,updatedAt,author",
                "--limit", "10",
                *repo_args,
            )
            issues = gh_json(
                "issue", "list",
                "--json", "number,title,state,updatedAt",
                "--limit", "10",
                *repo_args,
            )
        except GhError as exc:
            error_panel(str(exc))
            raise typer.Exit(1)

    # Format data
    pr_lines = "\n".join(
        f"- PR #{p['number']}: {p['title']} [{p['state']}]" for p in prs
    ) or "None"
    issue_lines = "\n".join(
        f"- Issue #{i['number']}: {i['title']} [{i['state']}]" for i in issues
    ) or "None"

    prompt = (
        f"Write a concise daily standup update based on this GitHub activity.\n"
        f"Include: what was done, what's in progress, any blockers.\n\n"
        f"Recent PRs:\n{pr_lines}\n\nOpen Issues:\n{issue_lines}"
    )

    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  console=console) as p:
        p.add_task(f"Generating standup with {ai_tool}…")
        if ai_tool == "gemini" and tool_available("gemini"):
            summary = _gemini(prompt)
        else:
            summary = (
                f"PRs:\n{pr_lines}\n\nIssues:\n{issue_lines}\n\n"
                "(AI summary skipped — gemini not available)"
            )

    ai_panel(summary, title="Daily Standup Summary", tool=ai_tool)
