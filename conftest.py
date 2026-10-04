"""Shared fixtures. Services (device, Redis) are only needed by live runs."""

from __future__ import annotations

import os
from typing import Any, Iterator

import pytest

from amtaf.drivers.api import DeviceApi
from amtaf.drivers.hardware import HardwareDriver
from amtaf.lock import BenchLock
from amtaf.runner.artifacts import RunContext, new_run_context
from amtaf.runner.failure import capture_failure

pytest_plugins = [
    "tests.existing.steps.gui_steps",
    "tests.existing.steps.hardware_steps",
]

DEVICE_URL = os.getenv("DEVICE_URL", "http://localhost:8080")


@pytest.fixture(scope="session")
def run_ctx() -> RunContext:
    return new_run_context()


@pytest.fixture(scope="session")
def bench_lock() -> Iterator[None]:
    """Hold the bench lock for the session when REDIS_URL is set."""
    url = os.getenv("REDIS_URL")
    if not url:
        yield
        return
    with BenchLock.from_url(url, bench=os.getenv("DEVICE_HOST", "localhost")):
        yield


@pytest.fixture(scope="session")
def device(bench_lock: None, run_ctx: RunContext) -> Iterator[HardwareDriver]:
    driver = HardwareDriver(
        host=os.getenv("DEVICE_HOST", "localhost"),
        port=int(os.getenv("DEVICE_SSH_PORT", "2222")),
        username=os.getenv("DEVICE_USER", "tester"),
        password=os.getenv("DEVICE_PASSWORD", "tester"),
        run_id=run_ctx.run_id,
    )
    yield driver
    driver.close()


@pytest.fixture(scope="session")
def api(run_ctx: RunContext) -> DeviceApi:
    return DeviceApi(DEVICE_URL, run_ctx.run_id)


@pytest.fixture
def console(run_ctx: RunContext) -> Iterator[Any]:
    from playwright.sync_api import sync_playwright

    from amtaf.drivers.gui import ConsolePage

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=os.getenv("HEADED") != "1")
        page = browser.new_page(extra_http_headers={"X-Run-Id": run_ctx.run_id})
        yield ConsolePage(page, DEVICE_URL)
        browser.close()


@pytest.fixture
def context() -> dict[str, str]:
    return {}


def pytest_bdd_step_error(
    request: Any,
    feature: Any,
    scenario: Any,
    step: Any,
    step_func: Any,
    step_func_args: Any,
    exception: Exception,
) -> None:
    capture_failure(request, request.getfixturevalue("run_ctx"), step, exception)
