"""Basic unit tests for devkit utilities."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ── config ────────────────────────────────────────────────────────────────────

def test_load_config_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr("devkit.config.CONFIG_FILE", tmp_path / "config.json")
    from devkit import config
    cfg = config.load_config()
    assert cfg["ai_tool"] in ("gemini", "copilot", "claude")
    assert "default_repo" in cfg


def test_save_and_load_config(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.json"
    monkeypatch.setattr("devkit.config.CONFIG_FILE", cfg_file)
    from devkit import config
    config.save_config({"ai_tool": "copilot", "theme": "light"})
    loaded = config.load_config()
    assert loaded["ai_tool"] == "copilot"
    assert loaded["theme"] == "light"


# ── gh wrapper ────────────────────────────────────────────────────────────────

def test_gh_success():
    from devkit.utils.gh import gh
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="hello\n", returncode=0)
        result = gh("--version")
    assert result == "hello"


def test_gh_json_parses_list():
    from devkit.utils.gh import gh_json
    payload = json.dumps([{"number": 1, "title": "Test issue"}])
    with patch("devkit.utils.gh.gh", return_value=payload):
        data = gh_json("issue", "list", "--json", "number,title")
    assert data[0]["title"] == "Test issue"


def test_gh_json_empty_returns_list():
    from devkit.utils.gh import gh_json
    with patch("devkit.utils.gh.gh", return_value=""):
        data = gh_json("issue", "list")
    assert data == []


# ── check tools ───────────────────────────────────────────────────────────────

def test_tool_available_true():
    from devkit.utils.check import tool_available
    # 'python3' or 'python' should always be present
    assert tool_available("python3") or tool_available("python")


def test_tool_available_false():
    from devkit.utils.check import tool_available
    assert not tool_available("__nonexistent_tool_xyz__")


def test_check_tools_raises_on_missing(monkeypatch):
    import shutil
    from devkit.utils import check
    monkeypatch.setattr(shutil, "which", lambda x: None)
    with pytest.raises(SystemExit):
        check.check_tools(["gh"])


# ── shell helpers ─────────────────────────────────────────────────────────────

def test_run_returns_stdout():
    from devkit.utils.shell import run
    out = run(["echo", "devkit"])
    assert out == "devkit"
