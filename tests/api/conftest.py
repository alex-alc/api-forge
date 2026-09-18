"""Fixtures for tests that talk to the SUT over HTTP.

Layered under the root conftest: sut_base_url is defined there and stays
visible here, while these fixtures are scoped to the API tests alone.
"""

from contextlib import suppress
from typing import TYPE_CHECKING

import httpx
import pytest
from faker import Faker

from api_forge.customers import Customer, CustomersService
from api_forge.payment_intents import PaymentIntentsService
from api_forge.response import UnexpectedStatusError

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


@pytest.fixture
def api_client(sut_base_url: str) -> "Iterator[httpx.Client]":
    """Provide an httpx.Client wired to the running SUT, closed after each test.

    Yields:
        An httpx.Client with base_url set to the SUT.

    """
    with httpx.Client(base_url=sut_base_url) as client:
        yield client


@pytest.fixture
def customers_service(api_client: httpx.Client) -> CustomersService:
    """Provide a CustomersService bound to the running SUT.

    Returns:
        A service client for the customer endpoints.

    """
    return CustomersService(api_client)


@pytest.fixture
def payment_intents_service(api_client: httpx.Client) -> PaymentIntentsService:
    """Provide a PaymentIntentsService bound to the running SUT.

    Returns:
        A service client for the payment intent endpoints.

    """
    return PaymentIntentsService(api_client)


@pytest.fixture
def make_customer(customers_service: CustomersService, faker: Faker) -> "Iterator[Callable[..., Customer]]":
    """Provide a factory that creates customers on the SUT and deletes them afterwards.

    The returned callable takes optional email and name overrides and falls back
    to Faker-generated values, so tests that do not care about the data can ignore it.

    Yields:
        A callable returning the created customer.

    """
    created_ids: list[str] = []

    def _make_customer(email: str | None = None, name: str | None = None) -> Customer:
        response = customers_service.create_customer(
            {
                "email": email or faker.unique.email(),
                "name": name or faker.name(),
            },
        )
        response.raise_for_error()
        customer = response.data
        if customer is None:
            message = "SUT returned a successful envelope with no customer payload"
            raise AssertionError(message)
        created_ids.append(customer.id)
        return customer

    yield _make_customer

    for customer_id in created_ids:
        with suppress(UnexpectedStatusError):
            customers_service.delete_customer(customer_id)
