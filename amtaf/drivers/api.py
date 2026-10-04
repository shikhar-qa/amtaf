"""API layer: thin REST client for the device."""

from __future__ import annotations

from typing import Any

import requests


class DeviceApi:
    """REST client. Sends X-Run-Id so device logs can be correlated."""

    def __init__(self, base_url: str, run_id: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if run_id:
            self.session.headers["X-Run-Id"] = run_id

    def get_settings(self) -> dict[str, Any]:
        """Return the device settings as seen through the API."""
        response = self.session.get(f"{self.base_url}/api/settings", timeout=10)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data

    def set_fault(self, enabled: bool) -> None:
        """Toggle the demo fault injection (UI says saved, nothing persisted)."""
        response = self.session.post(
            f"{self.base_url}/api/fault", json={"enabled": enabled}, timeout=10
        )
        response.raise_for_status()
