# Discovery — Modern CLI Tools

_Phase 1 deliverable: observations from hands-on tool exploration._

---

## gh — GitHub CLI

**What it does**: Replaces the GitHub browser UI entirely. You can create repos, manage issues,
review PRs, watch CI runs, call the REST/GraphQL API — all from the terminal.

**Surprising thing**: `gh api` gives raw access to every GitHub API endpoint, including GraphQL, 
which means you can craft highly specific queries (e.g. fetch only merged PRs from a specific 
contributor in the last 7 days) that the web UI doesn't expose.

**Use case I want to try**: `gh search issues` across multiple repos to build a unified inbox 
for a team.

---

## gh copilot — GitHub Copilot CLI

**What it does**: Translates natural language into shell commands (`suggest`) and explains 
existing commands in plain English (`explain`). Supports three targets: shell, git, and gh.

**Surprising thing**: The `--target gh` flag generates `gh` CLI commands from a description — 
e.g. "create a release from the latest tag" becomes a full `gh release create` invocation. 
It understands the gh CLI's own API surface.

**Use case I want to try**: Piping `git diff` output into `explain` to get a plain-English 
changelog for non-technical stakeholders.

---

## gemini — Google Gemini CLI

**What it does**: Brings Google Gemini AI to the terminal. Accepts text, files, and piped 
input. Particularly strong at summarisation and structured code review.

**Surprising thing**: Gemini's generous free tier means you can use it heavily in scripted 
pipelines without worrying about cost — unlike GPT-4 or Claude API usage without careful 
budget tracking.

**Use case I want to try**: Pipe `gh pr diff` output into Gemini to auto-generate a 
"What changed" section for PR descriptions before opening the PR.

---

## fzf — Fuzzy Finder

**What it does**: Turns any list piped to it into an interactive fuzzy-search selection menu.
Works with issues, git log, file lists, branch names — anything line-delimited.

**Surprising thing**: `--preview` flag lets you show a live preview panel while browsing. 
Combined with `gh issue view {1}` it creates a full TUI issue browser in one shell line.

**Use case I want to try**: Interactive branch switcher with `git branch | fzf` that shows 
the last commit of the highlighted branch in the preview pane.

---

## bat — Better cat

**What it does**: `cat` with syntax highlighting, line numbers, and git change markers. 
Supports 200+ languages and dozens of themes.

**Surprising thing**: `bat --diff` mode shows a coloured diff inline — useful as a `delta` 
alternative for quick one-file comparisons.

**Use case I want to try**: Replace all `cat` calls in devkit's display helpers with `bat` 
for richer code previews.

---

## delta — Better git diff

**What it does**: A pager for `git diff` with side-by-side mode, syntax highlighting, 
and word-level diff granularity.

**Surprising thing**: Delta integrates directly into `.gitconfig` as the default pager — 
every `git diff`, `git show`, and `git log -p` is automatically prettier with zero extra typing.

**Use case I want to try**: Use delta's `--side-by-side` mode in devkit's `pr-summary` 
command to show file diffs in a more readable format.

---

## atuin — Shell history

**What it does**: Replaces shell history with a SQLite database that supports full-text search, 
statistics, and optional encrypted sync across machines.

**Surprising thing**: `atuin stats` shows your most-used commands ranked by frequency — 
an immediate window into which parts of your workflow could be automated.

**Use case I want to try**: Query atuin's history to find all `gh` commands run in the last 
month and surface the most common patterns as devkit shortcut candidates.
