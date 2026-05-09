"""Subprocess helpers for the GitHub CLI (gh)."""

import json
import subprocess
from typing import Any


class GhError(RuntimeError):
    """Raised when a gh command returns a non-zero exit code."""


def gh(*args: str, check: bool = True) -> str:
    """Run `gh <args>` and return stdout as a stripped string."""
    try:
        result = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            check=check,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip()
        raise GhError(
            f"gh {' '.join(args)} failed:\n{stderr}"
        ) from exc


def gh_json(*args: str) -> Any:
    """Run a gh command and parse its JSON output."""
    raw = gh(*args)
    if not raw:
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GhError(f"Could not parse gh JSON output:\n{raw}") from exc
