# devkit

> AI-powered developer CLI toolkit — **gh · Gemini**

`devkit` est un meta-tool CLI Python qui orchestre GitHub CLI et Gemini CLI en un workflow développeur fluide et cohérent.

---

## Quick install

```bash
# 1. Clone
git clone https://github.com/yourname/devkit.git && cd devkit

# 2. Install (editable)
pip install -e .

# 3. Verify
devkit --help
```

### Prerequisites

| Tool | Install |
|------|---------|
| `gh` | https://cli.github.com |
| `fzf` | `brew install fzf` ou `apt install fzf` |
| `bat` | `brew install bat` ou `apt install bat` |
| `delta` | `brew install git-delta` |
| `gemini` | `npm install -g @google/gemini-cli` |

Authentification :
```bash
gh auth login
# Puis créer une clé sur https://aistudio.google.com/apikey
mkdir -p ~/.gemini && echo 'GEMINI_API_KEY=ta_clé' >> ~/.gemini/.env
```

---

## Command reference

### `devkit gh` — GitHub operations

```bash
# List open issues (rich table)
devkit gh issues

# List issues for a specific repo
devkit gh issues --repo cli/cli --limit 20

# Interactive issue picker (fzf → opens in browser)
devkit gh issues -i

# Full PR summary (title, body, changed files)
devkit gh pr-summary 42

# Create a feature branch and push it
devkit gh start-feature my-new-feature

# Open a PR for the current branch
devkit gh open-pr --title "feat: add dark mode"

# Show latest CI runs
devkit gh run-status
```

---

### `devkit ai` — AI tools (Gemini)

```bash
# Expliquer une commande shell
devkit ai explain "find . -name '*.py' -mtime -7 | xargs wc -l"

# Suggérer une commande depuis du langage naturel
devkit ai suggest "lister tous les containers docker triés par mémoire"
devkit ai suggest --target git "annuler le dernier commit en gardant les changements"
devkit ai suggest --target gh  "créer une release depuis le dernier tag"

# Review IA d'une PR
devkit ai review 42

# Générer un commit message depuis les changements stagés
git add -p
devkit ai commit

# Question libre
devkit ai ask "Quelle est la différence entre rebase et merge ?"
```

---

### `devkit workflow` — End-to-end workflows

```bash
# Full feature kickoff: branch + draft PR + AI implementation plan
devkit workflow feature-start my-feature
devkit workflow feature-start my-feature --issue 17   # links to issue #17

# AI review → confirm → squash-merge
devkit workflow pr-ship 42

# Daily standup summary from recent PRs/issues (Gemini)
devkit workflow daily-standup
devkit workflow daily-standup --repo myorg/myapp --days 2
```

---

### `devkit config` — Configuration

Config lives in `~/.devkit/config.json`.

```bash
devkit config show

devkit config set ai_tool gemini   # or: copilot
devkit config set default_repo myorg/myapp
devkit config set theme dark
```

---

## Architecture

```
devkit/
├── src/
│   └── devkit/
│       ├── main.py              # Root Typer app, command groups
│       ├── config.py            # ~/.devkit/config.json r/w
│       ├── commands/
│       │   ├── github.py        # Phase 2: issues, pr-summary, …
│       │   ├── ai.py            # Phase 3: explain, suggest, review, commit
│       │   └── workflow.py      # Phase 4: feature-start, pr-ship, daily-standup
│       └── utils/
│           ├── gh.py            # gh subprocess wrapper + JSON parsing
│           ├── shell.py         # Generic subprocess helpers
│           ├── display.py       # Rich formatters + fzf helper
│           └── check.py         # Tool availability checks at startup
├── tests/
├── discovery.md
├── pyproject.toml
└── README.md
```

### Design principles

- **Composability first** — every command is a thin wrapper; the real logic is in the tools it calls.
- **Fail loudly** — missing tools produce clear install instructions, not cryptic errors.
- **AI is optional** — every command degrades gracefully when AI tools are absent.
- **Config-driven** — preferred AI tool and default repo are read from `~/.devkit/config.json`.

---

## Demo

```
$ devkit workflow feature-start dark-mode --issue 23

──────────────── 🚀 Starting Feature ────────────────
✓ Branch created: feature/dark-mode
✓ Pushed to origin
✓ Draft PR: https://github.com/you/app/pull/44

╭─────────────── AI Implementation Plan ──────────────╮
│ 1. Add a `theme` field to the user settings model   │
│ 2. Create `src/styles/dark.css` with CSS variables  │
│ 3. Toggle class on <body> via a React context        │
│ 4. Persist preference to localStorage               │
│ Edge cases: system preference (prefers-color-scheme) │
╰──────────────────────────────────────────────────────╯

──────────────── ✓ Ready to code! ────────────────────
```

---

## Grading checklist

| Criterion | Status |
|-----------|--------|
| Tool integration (gh, copilot, gemini as subprocesses) | ✅ |
| `workflow feature-start` end-to-end | ✅ |
| Clean structure, typed functions | ✅ |
| Error handling (missing tools, bad IDs, network) | ✅ |
| Rich tables, panels, spinners | ✅ |
| README + installable package | ✅ |

---

## License

MIT
