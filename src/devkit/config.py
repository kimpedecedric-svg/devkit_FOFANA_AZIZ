"""devkit configuration — reads/writes ~/.devkit/config.json."""

import json
from pathlib import Path

CONFIG_FILE = Path.home() / ".devkit" / "config.json"

DEFAULTS: dict = {
    "ai_tool": "gemini",   # "gemini" | "copilot"
    "default_repo": "",
    "theme": "dark",
    "show_spinner": True,
}


def load_config() -> dict:
    """Load config, falling back to defaults for missing keys."""
    if CONFIG_FILE.exists():
        try:
            user = json.loads(CONFIG_FILE.read_text())
            return {**DEFAULTS, **user}
        except json.JSONDecodeError:
            pass
    return dict(DEFAULTS)


def save_config(cfg: dict) -> None:
    """Persist config to disk."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def get(key: str):
    """Convenience: read a single config value."""
    return load_config().get(key, DEFAULTS.get(key))
