"""Hardware/CLI layer: SSH driver with a command allowlist.

Generated tests may only run commands that match ``ALLOWED_COMMANDS``.
Anything else (reboot, flash, rm ...) is rejected before reaching the device.
"""

from __future__ import annotations

import re
from typing import Any

ALLOWED_COMMANDS = [
    re.compile(r"^cat /etc/device\.conf$"),
    re.compile(r"^tail -n \d{1,4} /var/log/device\.log$"),
    re.compile(r"^uname -a$"),
]


class CommandNotAllowed(Exception):
    pass


def check_command(command: str) -> None:
    if not any(pattern.match(command) for pattern in ALLOWED_COMMANDS):
        raise CommandNotAllowed(f"Command not in allowlist: {command!r}")


class HardwareDriver:
    """SSH access to the device under test (paramiko)."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        run_id: str | None = None,
    ) -> None:
        self.host, self.port = host, port
        self.username, self.password = username, password
        self.run_id = run_id
        self._client: Any = None

    def _connect(self) -> Any:
        if self._client is None:
            import paramiko

            client = paramiko.SSHClient()
            # Demo only: a real deployment should pin host keys.
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10,
            )
            self._client = client
        return self._client

    def run(self, command: str) -> str:
        """Run an allowlisted command and return stdout."""
        check_command(command)
        _, stdout, _ = self._connect().exec_command(command, timeout=15)
        return str(stdout.read().decode())

    def read_config(self) -> dict[str, str]:
        """Parse /etc/device.conf (key=value lines) into a dict."""
        config: dict[str, str] = {}
        for line in self.run("cat /etc/device.conf").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
        return config

    def tail_log(self, lines: int = 50) -> str:
        """Return the last ``lines`` lines of the device log."""
        return self.run(f"tail -n {lines} /var/log/device.log")

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
