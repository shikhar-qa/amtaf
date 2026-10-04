"""Failure hook: capture artifacts from every layer, then triage."""

from __future__ import annotations

from typing import Any

from amtaf.llm.client import RecordedClient, get_client
from amtaf.runner.artifacts import RunContext
from amtaf.triage.agent import triage, write_report


def capture_failure(request: Any, ctx: RunContext, step: Any, exc: Exception) -> None:
    """Best-effort capture. Each layer is isolated so one failure can't mask another."""
    ctx.save_text("failure.txt", f"run_id={ctx.run_id}\nstep: {step}\nerror: {exc!r}\n")
    captures = {
        "gui": lambda: request.getfixturevalue("console").screenshot(
            str(ctx.artifact_dir / "gui.png")
        ),
        "api": lambda: ctx.save_json(
            "api_settings.json", request.getfixturevalue("api").get_settings()
        ),
        "hardware": lambda: ctx.save_text(
            "device_state.txt",
            "config:\n"
            + str(request.getfixturevalue("device").read_config())
            + "\n\nlog tail:\n"
            + request.getfixturevalue("device").tail_log(50),
        ),
    }
    for name, capture in captures.items():
        try:
            capture()
        except Exception as capture_error:  # noqa: BLE001
            ctx.save_text(f"{name}_capture_error.txt", repr(capture_error))
    try:
        client = get_client()
        report_path = write_report(triage(ctx.artifact_dir, client), ctx.artifact_dir)
        text = report_path.read_text()
        if isinstance(client, RecordedClient):
            text = (
                "[RECORDED DEMO RESPONSE: canned text, not derived from this "
                "run's evidence. Set LLM_PROVIDER for real triage.]\n\n" + text
            )
            report_path.write_text(text)
        print("\n" + text)
        try:
            import allure

            allure.attach(
                text, name="AI root-cause analysis", attachment_type="text/plain"
            )
        except ImportError:
            pass
    except Exception as triage_error:  # noqa: BLE001
        ctx.save_text("triage_error.txt", repr(triage_error))
