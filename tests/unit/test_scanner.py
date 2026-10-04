from pathlib import Path

from amtaf.scanner.ast_index import index_methods, index_steps
from amtaf.scanner.matching import Decision, StepIndex

ROOT = Path(__file__).resolve().parents[2]


def test_indexes_existing_steps():
    steps = index_steps(ROOT / "tests" / "existing")
    assert {s.function for s in steps} >= {"logged_in", "set_syslog_server"}


def test_indexes_driver_methods():
    names = {m.qualified for m in index_methods(ROOT / "amtaf" / "drivers")}
    assert {"HardwareDriver.read_config", "ConsolePage.login"} <= names


def test_reuse_review_generate_decisions():
    index = StepIndex(index_steps(ROOT / "tests" / "existing"))
    reuse = index.match("I am logged in to the management console")
    assert reuse.decision is Decision.REUSE and reuse.score == 1.0
    reuse2 = index.match("I set the syslog server to 10.0.0.5 in the management UI")
    assert reuse2.decision is Decision.REUSE
    new = index.match(
        "the device config file has syslog server set to 10.0.0.5 within 10 seconds"
    )
    assert new.decision is Decision.GENERATE
