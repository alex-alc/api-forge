"""Shared behavior for resource service clients."""

from http import HTTPStatus

import httpx

from api_forge.response import ApiResponse, UnexpectedStatusError


class BaseService:
    """Base for service clients: holds the HTTP client and turns responses into envelopes."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    @staticmethod
    def _envelope[DataT](
        response: httpx.Response,
        data_type: type[DataT],
        expected_status: HTTPStatus,
    ) -> ApiResponse[DataT]:
        """Check a response against the expected status code and parse its envelope.

        Returns:
            The parsed response envelope.

        Raises:
            UnexpectedStatusError: If the status code differs from the expected one.

        """
        if response.status_code != expected_status:
            raise UnexpectedStatusError(expected_status, response)
        return ApiResponse[data_type].model_validate(response.json())
