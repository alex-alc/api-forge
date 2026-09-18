"""Response envelope returned by every api-forge service call."""

from enum import StrEnum

import httpx
from pydantic import BaseModel


class ErrorType(StrEnum):
    """Broad classes of API error, for use in assertions."""

    CONFLICT = "conflict"
    INVALID_REQUEST = "invalid_request"
    NOT_FOUND = "not_found"


class ErrorCode(StrEnum):
    """Error codes the API is expected to return, for use in assertions."""

    AMOUNT_TOO_SMALL = "amount_too_small"
    CUSTOMER_NOT_FOUND = "customer_not_found"
    CUSTOMER_REQUIRED = "customer_required"
    EMAIL_ALREADY_EXISTS = "email_already_exists"
    PARAMETER_INVALID = "parameter_invalid"
    PARAMETER_INVALID_ENUM = "parameter_invalid_enum"
    PARAMETER_INVALID_TYPE = "parameter_invalid_type"
    PARAMETER_MISSING = "parameter_missing"
    PARAMETER_OUT_OF_RANGE = "parameter_out_of_range"
    PARAMETER_UNKNOWN = "parameter_unknown"
    RESOURCE_MISSING = "resource_missing"


class ErrorDetail(BaseModel):
    """The error half of an API response.

    The fields stay plain strings rather than enums: an unknown code is a
    contract change the tests should report as a failed assertion, not as a
    parsing crash inside the client.

    Attributes:
        type: Broad class of the failure.
        code: The specific reason the request failed.
        message: Human-readable explanation.
        param: The offending field, when the failure is field-level.

    """

    type: str
    code: str
    message: str
    param: str | None = None


class ApiError(Exception):
    """Raised when an API response carries an error instead of a payload."""

    def __init__(self, error: ErrorDetail) -> None:
        super().__init__(f"{error.code}: {error.message}")
        self.error = error


class ApiResponse[DataT](BaseModel):
    """Envelope wrapping an API response payload or its error.

    Attributes:
        data: Response payload, or None when the call failed.
        error: Error details, or None when the call succeeded.

    """

    data: DataT | None = None
    error: ErrorDetail | None = None

    def raise_for_error(self) -> None:
        """Raise ApiError when the response carries an error.

        Raises:
            ApiError: If the error field is set.

        """
        if self.error is not None:
            raise ApiError(self.error)


class UnexpectedStatusError(Exception):
    """Raised when a response carries a status code the caller did not expect."""

    def __init__(self, expected_status: int, response: httpx.Response) -> None:
        super().__init__(f"expected status {expected_status}, got {response.status_code}: {response.text}")
