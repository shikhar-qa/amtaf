"""Existing GUI steps (seed library the scanner indexes for reuse)."""

from __future__ import annotations

from pytest_bdd import given, parsers, when

from amtaf.drivers.gui import ConsolePage


@given("I am logged in to the management console")
def logged_in(console: ConsolePage) -> None:
    """Log in with the default admin account."""
    console.login("admin", "admin")


@when(parsers.parse("I set the syslog server to {ip} in the management UI"))
def set_syslog_server(console: ConsolePage, ip: str) -> None:
    """Submit the syslog form and assert the UI confirms the save."""
    assert console.set_syslog_server(ip) == "Saved"
