"""Git safety: generated tests go to a feature branch, never straight to main."""

from __future__ import annotations

import subprocess
from pathlib import Path

PROTECTED = {"main", "master"}


def current_branch(repo: Path) -> str:
    out = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        cwd=repo,
        check=True,
    )
    return out.stdout.strip()


def create_feature_branch(repo: Path, name: str) -> str:
    """Create and switch to ``amtaf/<name>``. Refuses to use a protected name."""
    branch = f"amtaf/{name}"
    if branch in PROTECTED:
        raise ValueError("refusing to use a protected branch name")
    subprocess.run(["git", "checkout", "-b", branch], cwd=repo, check=True)
    return branch
