"""Existing hardware steps (seed library)."""

from __future__ import annotations

from pytest_bdd import parsers, then, when

from amtaf.drivers.hardware import HardwareDriver


@when(parsers.parse('I run "{command}" on the device'))
def run_command(device: HardwareDriver, command: str, context: dict[str, str]) -> None:
    """Run an allowlisted command and keep its output."""
    context["output"] = device.run(command)


@then(parsers.parse('the command output contains "{text}"'))
def output_contains(context: dict[str, str], text: str) -> None:
    """Assert the previous command output contains the text."""
    assert text in context["output"]
