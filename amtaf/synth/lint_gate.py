"""Static validation gate: generated code must pass black, flake8 and mypy."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LintResult:
    ok: bool
    details: str


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", *args], capture_output=True, text=True, cwd=cwd
    )


def run_gate(paths: list[Path], cwd: Path) -> LintResult:
    targets = [str(p) for p in paths]
    _run(["black", "-q", *targets], cwd)  # normalise formatting first
    checks = {
        "black": ["black", "--check", "-q", *targets],
        "flake8": ["flake8", "--max-line-length", "88", *targets],
        "mypy": [
            "mypy",
            "--ignore-missing-imports",
            "--follow-imports=silent",
            *targets,
        ],
    }
    problems = []
    for name, args in checks.items():
        result = _run(args, cwd)
        if result.returncode != 0:
            output = (result.stdout + result.stderr).strip()
            problems.append(f"[{name}] {output}")
    return LintResult(not problems, "\n".join(problems) or "black, flake8, mypy: ok")
