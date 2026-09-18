"""Service client for the customer endpoints."""

from datetime import datetime
from http import HTTPStatus

from pydantic import BaseModel

from api_forge import urls
from api_forge.response import ApiResponse
from api_forge.service import BaseService

CUSTOMER_ID_PREFIX = "cus_"


class Customer(BaseModel):
    """A customer as returned by the API.

    Attributes:
        id: Server-assigned identifier.
        email: The customer's email address.
        name: The customer's display name.
        created_at: When the customer was created.

    """

    id: str
    email: str
    name: str
    created_at: datetime


class CustomersService(BaseService):
    """Calls the customer endpoints.

    Every operation takes the status code the caller expects, defaulting to the
    happy path, and returns the parsed response envelope. Positive and negative
    cases therefore share one code path.
    """

    def create_customer(self, payload: object, expected_status: HTTPStatus = HTTPStatus.OK) -> ApiResponse[Customer]:
        """Create a customer from any payload.

        Returns:
            The parsed response envelope.

        """
        response = self._client.post(urls.CUSTOMERS, json=payload)
        return self._envelope(response, Customer, expected_status)

    def get_customer(self, customer_id: str, expected_status: HTTPStatus = HTTPStatus.OK) -> ApiResponse[Customer]:
        """Fetch a single customer by id.

        Returns:
            The parsed response envelope.

        """
        response = self._client.get(urls.customer(customer_id))
        return self._envelope(response, Customer, expected_status)

    def delete_customer(self, customer_id: str, expected_status: HTTPStatus = HTTPStatus.OK) -> ApiResponse[Customer]:
        """Delete a customer by id.

        Returns:
            The parsed response envelope.

        """
        response = self._client.delete(urls.customer(customer_id))
        return self._envelope(response, Customer, expected_status)
