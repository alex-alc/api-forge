"""Tests for the SUT's health endpoint."""

from http import HTTPStatus

import httpx


def test_health_returns_ok(api_client: httpx.Client) -> None:
    response = api_client.get("/health")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}


def test_health_rejects_post(api_client: httpx.Client) -> None:
    response = api_client.post("/health")

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
