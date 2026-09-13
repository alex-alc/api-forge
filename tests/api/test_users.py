"""Tests for the SUT's user endpoints."""

from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from faker import Faker

from api_forge.users import UsersService

if TYPE_CHECKING:
    from collections.abc import Callable

    from api_forge.users import UserDto

UNKNOWN_USER_ID = "00000000-0000-0000-0000-000000000000"


def test_create_user_returns_the_created_user(
    make_user: "Callable[..., UserDto]",
    faker: Faker,
) -> None:
    email = faker.unique.email()
    name = faker.name()

    user = make_user(email=email, name=name)

    assert user.email == email
    assert user.name == name
    assert user.id


@pytest.mark.parametrize(
    ("payload", "expected_field"),
    [
        pytest.param({"email": "not-an-email", "name": "Ada"}, "body.email", id="malformed_email"),
        pytest.param({"email": "ada@example.com", "name": 42}, "body.name", id="name_not_a_string"),
        pytest.param({"email": "ada@example.com"}, "body.name", id="missing_name"),
        pytest.param({"name": "Ada"}, "body.email", id="missing_email"),
        pytest.param({}, "body.email", id="empty_payload"),
    ],
)
def test_create_user_rejects_an_invalid_payload(
    users_service: UsersService,
    payload: dict[str, object],
    expected_field: str,
) -> None:
    response = users_service.create_user(payload, HTTPStatus.UNPROCESSABLE_ENTITY)

    assert response.data is None
    assert response.error is not None
    assert expected_field in response.error


def test_get_user_returns_the_stored_user(
    users_service: UsersService,
    make_user: "Callable[..., UserDto]",
) -> None:
    user = make_user()

    response = users_service.get_user(user.id)

    assert response.error is None
    assert response.data == user


def test_get_user_reports_an_unknown_id(users_service: UsersService) -> None:
    response = users_service.get_user(UNKNOWN_USER_ID, HTTPStatus.NOT_FOUND)

    assert response.data is None
    assert response.error is not None
    assert UNKNOWN_USER_ID in response.error


def test_delete_user_removes_it(
    users_service: UsersService,
    make_user: "Callable[..., UserDto]",
) -> None:
    user = make_user()

    response = users_service.delete_user(user.id)

    assert response.error is None
    assert users_service.get_user(user.id, HTTPStatus.NOT_FOUND).data is None


def test_delete_user_reports_an_unknown_id(users_service: UsersService) -> None:
    response = users_service.delete_user(UNKNOWN_USER_ID, HTTPStatus.NOT_FOUND)

    assert response.data is None
    assert response.error is not None
    assert UNKNOWN_USER_ID in response.error
