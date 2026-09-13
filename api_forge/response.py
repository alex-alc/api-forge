"""Response envelope returned by every api-forge service call."""

import httpx
from pydantic import BaseModel


class ApiError(Exception):
    """Raised when an API response carries an error instead of a payload."""


class ApiResponse[DataT](BaseModel):
    """Envelope wrapping an API response payload or its error.

    Attributes:
        data: Response payload, or None when the call failed.
        error: Error message, or None when the call succeeded.

    """

    data: DataT | None = None
    error: str | None = None

    def raise_for_error(self) -> None:
        """Raise ApiError when the response carries an error message.

        Raises:
            ApiError: If the error field is set.

        """
        if self.error is not None:
            raise ApiError(self.error)


class UnexpectedStatusError(Exception):
    """Raised when a response carries a status code the caller did not expect."""

    def __init__(self, expected_status: int, response: httpx.Response) -> None:
        super().__init__(f"expected status {expected_status}, got {response.status_code}: {response.text}")
