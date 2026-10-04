"""Typed Task Graph: the contract between the LLM and the rest of the system."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Layer(str, Enum):
    GUI = "GUI"
    API = "API"
    HARDWARE_CLI = "HARDWARE_CLI"


class Step(BaseModel):
    id: str
    layer: Layer
    keyword: Literal["Given", "When", "Then"]
    action: str
    gherkin: str = Field(description="Declarative Gherkin step text, no keyword")
    expected: str | None = None
    sla_seconds: float | None = None
    sla_source: Literal["explicit", "inferred"] = "explicit"
    depends_on: list[str] = Field(default_factory=list)

    @property
    def needs_confirmation(self) -> bool:
        """Inferred SLAs are model guesses, so a human must confirm them."""
        return self.sla_seconds is not None and self.sla_source == "inferred"


class TaskGraph(BaseModel):
    intent: str
    preconditions: list[str] = Field(default_factory=list)
    steps: list[Step]

    @model_validator(mode="after")
    def _check_graph(self) -> "TaskGraph":
        seen: set[str] = set()
        for step in self.steps:
            if step.id in seen:
                raise ValueError(f"duplicate step id {step.id}")
            missing = [d for d in step.depends_on if d not in seen]
            if missing:
                raise ValueError(f"{step.id} depends on unknown/later steps {missing}")
            seen.add(step.id)
        if not self.steps:
            raise ValueError("task graph has no steps")
        return self

    def layers(self) -> list[Layer]:
        ordered: list[Layer] = []
        for step in self.steps:
            if step.layer not in ordered:
                ordered.append(step.layer)
        return ordered

    def pending_confirmations(self) -> list[Step]:
        return [s for s in self.steps if s.needs_confirmation]
