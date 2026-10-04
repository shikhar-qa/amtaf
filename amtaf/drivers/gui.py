"""GUI layer: Page Object for the management console (Playwright)."""

from __future__ import annotations

from typing import Any


class ConsolePage:
    """Page Object Model. ``page`` is a Playwright sync ``Page``."""

    def __init__(self, page: Any, base_url: str) -> None:
        self.page = page
        self.base_url = base_url.rstrip("/")

    def login(self, username: str, password: str) -> None:
        """Log in to the management console."""
        self.page.goto(f"{self.base_url}/login")
        self.page.fill("#username", username)
        self.page.fill("#password", password)
        self.page.click("#login")
        self.page.wait_for_url("**/settings")

    def set_syslog_server(self, ip: str) -> str:
        """Submit the syslog form and return the status banner text."""
        self.page.fill("#syslog_server", ip)
        self.page.click("#save")
        self.page.wait_for_selector("#status")
        return str(self.page.inner_text("#status"))

    def screenshot(self, path: str) -> None:
        self.page.screenshot(path=path)
