"""Unit tests for the ApiResponse envelope."""

import pytest

from api_forge.response import ApiError, ApiResponse


def test_raise_for_error_is_noop_on_successful_response() -> None:
    response: ApiResponse[dict[str, int]] = ApiResponse(data={"id": 1})

    response.raise_for_error()

    assert response.data == {"id": 1}
    assert response.error is None


def test_raise_for_error_raises_when_error_is_set() -> None:
    response: ApiResponse[dict[str, int]] = ApiResponse(error="not found")

    with pytest.raises(ApiError, match="not found"):
        response.raise_for_error()

    assert response.data is None
