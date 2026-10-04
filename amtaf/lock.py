"""Hardware bench mutex: one run per physical device at a time.

Uses a Redis lock with a TTL, so a crashed worker cannot hold a bench forever.
"""

from __future__ import annotations

from typing import Any

from redis.exceptions import LockError


class BenchBusy(Exception):
    pass


class BenchLock:
    def __init__(
        self, client: Any, bench: str, ttl: float = 300, wait: float = 60
    ) -> None:
        self._lock = client.lock(
            f"amtaf:bench:{bench}", timeout=ttl, blocking_timeout=wait
        )
        self.bench = bench

    @classmethod
    def from_url(cls, url: str, bench: str, **kwargs: Any) -> "BenchLock":
        import redis

        return cls(redis.Redis.from_url(url), bench, **kwargs)

    def __enter__(self) -> "BenchLock":
        if not self._lock.acquire():
            raise BenchBusy(f"Bench '{self.bench}' is in use by another run")
        return self

    def __exit__(self, *exc: object) -> None:
        try:
            self._lock.release()
        except LockError:  # TTL already expired or lock not owned
            pass
