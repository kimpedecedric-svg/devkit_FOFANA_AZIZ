"""Generic subprocess helpers."""

import subprocess
from typing import Sequence


def run(cmd: Sequence[str], input_text: str = "", check: bool = True) -> str:
    """Run a command, return stdout. Raises on non-zero exit when check=True."""
    result = subprocess.run(
        list(cmd),
        input=input_text or None,
        capture_output=True,
        text=True,
        check=check,
    )
    return result.stdout.strip()


def run_passthrough(cmd: Sequence[str]) -> int:
    """Run a command with inherited stdio (for interactive tools). Returns exit code."""
    result = subprocess.run(list(cmd))
    return result.returncode


def pipe(source_cmd: Sequence[str], dest_cmd: Sequence[str]) -> str:
    """Pipe stdout of source_cmd into dest_cmd, return final stdout."""
    p1 = subprocess.Popen(list(source_cmd), stdout=subprocess.PIPE, text=True)
    p2 = subprocess.Popen(
        list(dest_cmd),
        stdin=p1.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if p1.stdout:
        p1.stdout.close()
    out, _ = p2.communicate()
    return out.strip()
