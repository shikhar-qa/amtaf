"""Per-run artifact directory and shared run id (cross-layer correlation)."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RunContext:
    run_id: str
    artifact_dir: Path

    def save_text(self, name: str, text: str) -> Path:
        path = self.artifact_dir / name
        path.write_text(text)
        return path

    def save_json(self, name: str, data: Any) -> Path:
        return self.save_text(name, json.dumps(data, indent=2, default=str))


def new_run_context(base: Path = Path("artifacts")) -> RunContext:
    run_id = uuid.uuid4().hex[:8]
    directory = base / run_id
    directory.mkdir(parents=True, exist_ok=True)
    return RunContext(run_id, directory)
