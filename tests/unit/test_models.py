import pytest
from pydantic import ValidationError

from amtaf.orchestrator.models import Layer, Step, TaskGraph


def step(sid: str, deps: list[str] | None = None, **kw) -> Step:
    return Step(
        id=sid,
        layer=Layer.API,
        keyword="When",
        action="a",
        gherkin="g",
        depends_on=deps or [],
        **kw,
    )


def test_valid_graph():
    graph = TaskGraph(intent="x", steps=[step("s1"), step("s2", ["s1"])])
    assert graph.layers() == [Layer.API]


def test_rejects_unknown_dependency():
    with pytest.raises(ValidationError):
        TaskGraph(intent="x", steps=[step("s1", ["s9"])])


def test_rejects_duplicate_ids():
    with pytest.raises(ValidationError):
        TaskGraph(intent="x", steps=[step("s1"), step("s1")])


def test_inferred_sla_needs_confirmation():
    graph = TaskGraph(
        intent="x",
        steps=[
            step("s1", sla_seconds=5, sla_source="inferred"),
            step("s2", sla_seconds=5, sla_source="explicit"),
        ],
    )
    assert [s.id for s in graph.pending_confirmations()] == ["s1"]
