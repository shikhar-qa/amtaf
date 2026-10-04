"""Orchestrator: plain English -> validated Task Graph."""

from __future__ import annotations

from amtaf.llm.client import LLMClient
from amtaf.orchestrator.models import TaskGraph

PROMPT = """You are the orchestrator of a multi-layer test framework.
Decompose the test intent below into an ordered task graph.

Rules:
- Tag every step with one layer: GUI, API or HARDWARE_CLI.
- Write each step's `gherkin` as a short declarative sentence without the
  Given/When/Then keyword, keeping literal values (IPs, numbers) inline.
- Use sla_source="explicit" only when the intent states the time bound.
  If you infer a bound, set sla_source="inferred".
- Do not invent steps the intent does not require.

Test intent:
{intent}
"""


def plan(intent: str, client: LLMClient) -> TaskGraph:
    return client.structured(PROMPT.format(intent=intent), TaskGraph, key="plan")
