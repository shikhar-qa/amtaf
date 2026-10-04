"""Triage agent: reads captured artifacts, proposes a root cause with confidence."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from amtaf.llm.client import LLMClient
from amtaf.orchestrator.models import Layer

PROMPT = """You are a test failure triage agent. Using ONLY the evidence below,
identify which layer most likely failed and why. Entries share a run id, so
correlate across layers. If the evidence is insufficient, say so and use
low confidence. Do not invent evidence.

{evidence}
"""


class RCAReport(BaseModel):
    failing_layer: Layer
    summary: str
    confidence: Literal["low", "medium", "high"]
    evidence: list[str]
    suggested_next_step: str


def collect_evidence(artifact_dir: Path, limit: int = 4000) -> str:
    parts = []
    for path in sorted(artifact_dir.glob("*")):
        if path.suffix in {".txt", ".json", ".log"}:
            parts.append(f"=== {path.name} ===\n{path.read_text()[:limit]}")
    return "\n\n".join(parts)


def triage(artifact_dir: Path, client: LLMClient) -> RCAReport:
    prompt = PROMPT.format(evidence=collect_evidence(artifact_dir))
    return client.structured(prompt, RCAReport, key="triage")


def write_report(report: RCAReport, artifact_dir: Path) -> Path:
    lines = [
        "# Root-cause analysis",
        f"- **Likely failing layer:** {report.failing_layer.value}",
        f"- **Confidence:** {report.confidence}",
        "",
        report.summary,
        "",
        "## Evidence",
        *[f"- {item}" for item in report.evidence],
        "",
        f"**Suggested next step:** {report.suggested_next_step}",
        "",
        "_AI-generated; review before filing a defect._",
    ]
    path = artifact_dir / "rca.md"
    path.write_text("\n".join(lines) + "\n")
    return path
