"""
devkit gh — GitHub CLI commands
Phase 2: issues, pr-summary, start-feature, open-pr, run-status
"""

from __future__ import annotations

import subprocess

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from devkit.utils.check import check_tools
from devkit.utils.display import console, error_panel, fzf_select
from devkit.utils.gh import GhError, gh, gh_json

app = typer.Typer(help="GitHub operations (issues, PRs, branches…)")


# ── helpers ──────────────────────────────────────────────────────────────────

def _repo_args(repo: str) -> list[str]:
    return ["--repo", repo] if repo else []


# ── commands ─────────────────────────────────────────────────────────────────

@app.command()
def issues(
    repo: str = typer.Option("", help="owner/repo (default: current repo)"),
    limit: int = typer.Option(15, help="Max number of issues to fetch"),
    interactive: bool = typer.Option(False, "--interactive", "-i",
                                      help="Pick an issue with fzf and open in browser"),
):
    """List open issues as a rich table."""
    check_tools(["gh"])
    try:
        data = gh_json(
            "issue", "list",
            "--json", "number,title,state,labels,assignees",
            "--limit", str(limit),
            *_repo_args(repo),
        )
    except GhError as exc:
        error_panel(str(exc), "gh error")
        raise typer.Exit(1)

    if not data:
        console.print("[muted]No open issues found.[/muted]")
        return

    if interactive:
        lines = [f"#{i['number']} {i['title']}" for i in data]
        selected = fzf_select(lines, prompt="Issue > ")
        if selected:
            issue_num = selected.split()[0].lstrip("#")
            gh("issue", "view", issue_num, "--web", *_repo_args(repo), check=False)
        return

    table = Table(title="Open Issues", border_style="green", show_lines=True)
    table.add_column("#", style="cyan", width=6, justify="right")
    table.add_column("Title", min_width=35)
    table.add_column("Labels", width=22)
    table.add_column("Assignees", width=18)

    for issue in data:
        labels = ", ".join(lbl["name"] for lbl in issue.get("labels", [])) or "—"
        assignees = ", ".join(a["login"] for a in issue.get("assignees", [])) or "—"
        table.add_row(str(issue["number"]), issue["title"], labels, assignees)

    console.print(table)


@app.command(name="pr-summary")
def pr_summary(
    pr_number: int = typer.Argument(..., help="PR number"),
    repo: str = typer.Option("", help="owner/repo (default: current repo)"),
):
    """Show PR title, body, and changed files."""
    check_tools(["gh"])
    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  console=console) as progress:
        t = progress.add_task("Fetching PR info…")
        try:
            info = gh_json(
                "pr", "view", str(pr_number),
                "--json", "number,title,body,author,state,changedFiles,additions,deletions",
                *_repo_args(repo),
            )
            progress.update(t, description="Fetching changed files…")
            files_raw = gh(
                "pr", "view", str(pr_number), "--json", "files",
                *_repo_args(repo),
            )
        except GhError as exc:
            error_panel(str(exc), "gh error")
            raise typer.Exit(1)

    import json as _json
    files = _json.loads(files_raw).get("files", [])

    console.rule(f"[bold cyan]PR #{info['number']} — {info['title']}[/bold cyan]")
    console.print(f"[muted]Author:[/muted] {info['author']['login']}  "
                  f"[muted]State:[/muted] {info['state']}  "
                  f"[success]+{info['additions']}[/success] "
                  f"[error]-{info['deletions']}[/error]")
    if info.get("body"):
        console.print(f"\n{info['body']}\n")

    if files:
        table = Table(title="Changed Files", border_style="cyan")
        table.add_column("File", min_width=40)
        table.add_column("+", style="green", justify="right", width=6)
        table.add_column("-", style="red", justify="right", width=6)
        for f in files:
            table.add_row(f["path"], str(f.get("additions", 0)), str(f.get("deletions", 0)))
        console.print(table)


@app.command(name="start-feature")
def start_feature(
    name: str = typer.Argument(..., help="Branch name (kebab-case)"),
):
    """Create and push a new feature branch."""
    check_tools(["gh", "git"])
    branch = f"feature/{name}"
    try:
        subprocess.run(["git", "checkout", "-b", branch], check=True)
        console.print(f"[success]✓[/success] Branch created: [cyan]{branch}[/cyan]")
        subprocess.run(["git", "push", "-u", "origin", branch], check=True)
        console.print(f"[success]✓[/success] Pushed to origin/{branch}")
    except subprocess.CalledProcessError as exc:
        error_panel(str(exc), "Git error")
        raise typer.Exit(1)


@app.command(name="open-pr")
def open_pr(
    title: str = typer.Option("", help="PR title (prompted if empty)"),
    body: str = typer.Option("", help="PR body"),
    draft: bool = typer.Option(True, help="Create as draft PR"),
):
    """Create a PR for the current branch."""
    check_tools(["gh"])
    if not title:
        title = typer.prompt("PR title")
    if not body:
        body = typer.prompt("PR body (optional)", default="")

    args = ["pr", "create", "--title", title, "--body", body or ""]
    if draft:
        args.append("--draft")
    try:
        url = gh(*args)
        console.print(f"[success]✓[/success] PR created: {url}")
    except GhError as exc:
        error_panel(str(exc), "gh error")
        raise typer.Exit(1)


@app.command(name="run-status")
def run_status(
    repo: str = typer.Option("", help="owner/repo (default: current repo)"),
    limit: int = typer.Option(10, help="Number of runs to show"),
):
    """Show latest CI run statuses."""
    check_tools(["gh"])
    try:
        data = gh_json(
            "run", "list",
            "--json", "databaseId,displayTitle,status,conclusion,headBranch,createdAt",
            "--limit", str(limit),
            *_repo_args(repo),
        )
    except GhError as exc:
        error_panel(str(exc), "gh error")
        raise typer.Exit(1)

    if not data:
        console.print("[muted]No runs found.[/muted]")
        return

    STATUS_STYLE = {
        "success": "[green]✓ success[/green]",
        "failure": "[red]✗ failure[/red]",
        "cancelled": "[yellow]⊘ cancelled[/yellow]",
        None: "[dim]…[/dim]",
    }

    table = Table(title="CI Run Status", border_style="blue")
    table.add_column("ID", style="dim", width=10)
    table.add_column("Title", min_width=30)
    table.add_column("Branch", width=20)
    table.add_column("Status", width=16)

    for run in data:
        conclusion = run.get("conclusion")
        status_str = (
            STATUS_STYLE.get(conclusion, f"[cyan]{run['status']}[/cyan]")
            if run["status"] == "completed"
            else f"[cyan]{run['status']}[/cyan]"
        )
        table.add_row(
            str(run["databaseId"]),
            run["displayTitle"][:45],
            run["headBranch"],
            status_str,
        )
    console.print(table)
