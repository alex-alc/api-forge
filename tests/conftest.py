"""Shared fixtures for the api-forge test suite.

Boots the framework's system under test (a FastAPI service, run for real
under uvicorn) once per test session, and hands out an httpx.Client wired
to it per test.
"""

import socket
import threading
import time
from http import HTTPStatus
from typing import TYPE_CHECKING

import httpx
import pytest
import uvicorn

from sut.app import app

if TYPE_CHECKING:
    from collections.abc import Iterator

HEALTH_CHECK_TIMEOUT_SECONDS = 5.0
HEALTH_CHECK_POLL_INTERVAL_SECONDS = 0.05
LOG_LEVEL = "warning"


def _free_port() -> int:
    """Find a free TCP port on localhost.

    Returns:
        An unused port number.

    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_until_ready(base_url: str) -> None:
    """Poll the SUT's health endpoint until it responds or the timeout elapses.

    Raises:
        TimeoutError: If the SUT does not become ready in time.

    """
    deadline = time.monotonic() + HEALTH_CHECK_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        try:
            response = httpx.get(f"{base_url}/health", timeout=HEALTH_CHECK_POLL_INTERVAL_SECONDS)
        except httpx.TransportError:
            time.sleep(HEALTH_CHECK_POLL_INTERVAL_SECONDS)
            continue
        if response.status_code == HTTPStatus.OK:
            return
        time.sleep(HEALTH_CHECK_POLL_INTERVAL_SECONDS)
    raise TimeoutError(f"SUT did not become ready at {base_url} within {HEALTH_CHECK_TIMEOUT_SECONDS}s")


@pytest.fixture(scope="session")
def sut_base_url() -> "Iterator[str]":
    """Run the FastAPI SUT under uvicorn in a background thread for the whole session.

    Yields:
        The base URL the SUT is listening on.

    """
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level=LOG_LEVEL)
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    _wait_until_ready(base_url)

    yield base_url

    server.should_exit = True
    thread.join()


@pytest.fixture
def api_client(sut_base_url: str) -> "Iterator[httpx.Client]":
    """Provide an httpx.Client wired to the running SUT, closed after each test.

    Yields:
        An httpx.Client with base_url set to the SUT.

    """
    with httpx.Client(base_url=sut_base_url) as client:
        yield client
