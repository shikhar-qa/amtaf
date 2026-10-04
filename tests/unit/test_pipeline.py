"""Offline end-to-end: English -> task graph -> reuse scan -> synthesis -> lint."""

from pathlib import Path

from amtaf.cli import generate
from amtaf.llm.client import RecordedClient
from amtaf.scanner.matching import Decision

ROOT = Path(__file__).resolve().parents[2]
INTENT = (
    "Set the syslog server to 10.0.0.5 in the management UI and verify it "
    "was applied on the device within 10 seconds."
)


def test_generate_reuses_and_synthesizes_minimum(tmp_path):
    out = tmp_path / "generated"
    result = generate(INTENT, ROOT, client=RecordedClient(), out_dir=out)
    decisions = {k: m.decision for k, m in result.matches.items()}
    assert decisions == {
        "s1": Decision.REUSE,
        "s2": Decision.REUSE,
        "s3": Decision.GENERATE,
    }
    assert len(result.generated) == 1
    feature = (out / next(p.name for p in out.glob("*.feature"))).read_text()
    assert "@layer=gui @layer=hardware" in feature
    assert "Given I am logged in" in feature and "Then the device config" in feature
    assert result.lint is not None and result.lint.ok, result.lint.details
