"""Unit tests for the ApiResponse envelope."""

import pytest

from api_forge.response import ApiError, ApiResponse, ErrorCode, ErrorDetail, ErrorType

NOT_FOUND_ERROR = ErrorDetail(
    type=ErrorType.NOT_FOUND,
    code=ErrorCode.RESOURCE_MISSING,
    message="No such customer: cus_1",
    param="id",
)


def test_raise_for_error_is_noop_on_successful_response() -> None:
    response: ApiResponse[dict[str, int]] = ApiResponse(data={"id": 1})

    response.raise_for_error()

    assert response.data == {"id": 1}
    assert response.error is None


def test_raise_for_error_raises_when_error_is_set() -> None:
    response: ApiResponse[dict[str, int]] = ApiResponse(error=NOT_FOUND_ERROR)

    with pytest.raises(ApiError) as raised:
        response.raise_for_error()

    assert raised.value.error.code == ErrorCode.RESOURCE_MISSING
    assert raised.value.error.param == "id"
    assert response.data is None
