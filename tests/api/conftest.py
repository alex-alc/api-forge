"""Fixtures for tests that talk to the SUT over HTTP.

Layered under the root conftest: sut_base_url is defined there and stays
visible here, while these fixtures are scoped to the API tests alone.
"""

from contextlib import suppress
from typing import TYPE_CHECKING

import httpx
import pytest
from faker import Faker

from api_forge.response import UnexpectedStatusError
from api_forge.users import UserDto, UsersService

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
def users_service(api_client: httpx.Client) -> UsersService:
    """Provide a UsersService bound to the running SUT.

    Returns:
        A service client for the user endpoints.

    """
    return UsersService(api_client)


@pytest.fixture
def make_user(users_service: UsersService, faker: Faker) -> "Iterator[Callable[..., UserDto]]":
    """Provide a factory that creates users on the SUT and deletes them afterwards.

    The returned callable takes optional email and name overrides and falls back
    to Faker-generated values, so tests that do not care about the data can ignore it.

    Yields:
        A callable returning the created user's payload.

    """
    created_ids: list[str] = []

    def _make_user(email: str | None = None, name: str | None = None) -> UserDto:
        response = users_service.create_user(
            {
                "email": email or faker.unique.email(),
                "name": name or faker.name(),
            },
        )
        response.raise_for_error()
        user = response.data
        if user is None:
            message = "SUT returned a successful envelope with no user payload"
            raise AssertionError(message)
        created_ids.append(user.id)
        return user

    yield _make_user

    for user_id in created_ids:
        with suppress(UnexpectedStatusError):
            users_service.delete_user(user_id)
