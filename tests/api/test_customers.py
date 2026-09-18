"""Tests for the SUT's customer endpoints."""

from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from faker import Faker

from api_forge.customers import CUSTOMER_ID_PREFIX, CustomersService
from api_forge.response import ErrorCode, ErrorType

if TYPE_CHECKING:
    from collections.abc import Callable

    from api_forge.customers import Customer

UNKNOWN_CUSTOMER_ID = "cus_00000000000000000000000000000000"


def test_create_customer_returns_the_created_customer(
    make_customer: "Callable[..., Customer]",
    faker: Faker,
) -> None:
    email = faker.unique.email()
    name = faker.name()

    customer = make_customer(email=email, name=name)

    assert customer.email == email
    assert customer.name == name
    assert customer.id.startswith(CUSTOMER_ID_PREFIX)


def test_create_customer_lowercases_the_whole_email(
    make_customer: "Callable[..., Customer]",
    faker: Faker,
) -> None:
    email = faker.unique.email()

    customer = make_customer(email=email.upper())

    assert customer.email == email.lower()


def test_create_customer_rejects_a_duplicate_email(
    customers_service: CustomersService,
    make_customer: "Callable[..., Customer]",
    faker: Faker,
) -> None:
    email = faker.unique.email()
    make_customer(email=email)

    response = customers_service.create_customer({"email": email, "name": faker.name()}, HTTPStatus.CONFLICT)

    assert response.data is None
    assert response.error is not None
    assert response.error.type == ErrorType.CONFLICT
    assert response.error.code == ErrorCode.EMAIL_ALREADY_EXISTS
    assert response.error.param == "email"


def test_create_customer_treats_a_differently_cased_email_as_taken(
    customers_service: CustomersService,
    make_customer: "Callable[..., Customer]",
    faker: Faker,
) -> None:
    email = faker.unique.email()
    make_customer(email=email)

    response = customers_service.create_customer({"email": email.upper(), "name": faker.name()}, HTTPStatus.CONFLICT)

    assert response.data is None
    assert response.error is not None
    assert response.error.code == ErrorCode.EMAIL_ALREADY_EXISTS


def test_deleting_a_customer_frees_its_email(
    customers_service: CustomersService,
    make_customer: "Callable[..., Customer]",
    faker: Faker,
) -> None:
    email = faker.unique.email()
    original = make_customer(email=email)
    customers_service.delete_customer(original.id)

    recreated = make_customer(email=email)

    assert recreated.email == email
    assert recreated.id != original.id


@pytest.mark.parametrize(
    ("payload", "expected_code", "expected_param"),
    [
        pytest.param(
            {"email": "not-an-email", "name": "Ada"},
            ErrorCode.PARAMETER_INVALID,
            "email",
            id="malformed_email",
        ),
        pytest.param(
            {"email": "ada@example.com", "name": 42},
            ErrorCode.PARAMETER_INVALID_TYPE,
            "name",
            id="name_not_a_string",
        ),
        pytest.param(
            {"email": "ada@example.com"},
            ErrorCode.PARAMETER_MISSING,
            "name",
            id="missing_name",
        ),
        pytest.param(
            {"name": "Ada"},
            ErrorCode.PARAMETER_MISSING,
            "email",
            id="missing_email",
        ),
        pytest.param(
            {},
            ErrorCode.PARAMETER_MISSING,
            "email",
            id="empty_payload",
        ),
        pytest.param(
            {"email": "ada@example.com", "name": "Ada", "nickname": "adz"},
            ErrorCode.PARAMETER_UNKNOWN,
            "nickname",
            id="unknown_field",
        ),
    ],
)
def test_create_customer_rejects_an_invalid_payload(
    customers_service: CustomersService,
    payload: dict[str, object],
    expected_code: ErrorCode,
    expected_param: str,
) -> None:
    response = customers_service.create_customer(payload, HTTPStatus.UNPROCESSABLE_ENTITY)

    assert response.data is None
    assert response.error is not None
    assert response.error.type == ErrorType.INVALID_REQUEST
    assert response.error.code == expected_code
    assert response.error.param == expected_param


def test_get_customer_returns_the_stored_customer(
    customers_service: CustomersService,
    make_customer: "Callable[..., Customer]",
) -> None:
    customer = make_customer()

    response = customers_service.get_customer(customer.id)

    assert response.error is None
    assert response.data == customer


def test_get_customer_reports_an_unknown_id(customers_service: CustomersService) -> None:
    response = customers_service.get_customer(UNKNOWN_CUSTOMER_ID, HTTPStatus.NOT_FOUND)

    assert response.data is None
    assert response.error is not None
    assert response.error.type == ErrorType.NOT_FOUND
    assert response.error.code == ErrorCode.RESOURCE_MISSING
    assert UNKNOWN_CUSTOMER_ID in response.error.message


def test_delete_customer_removes_it(
    customers_service: CustomersService,
    make_customer: "Callable[..., Customer]",
) -> None:
    customer = make_customer()

    response = customers_service.delete_customer(customer.id)

    assert response.error is None
    assert customers_service.get_customer(customer.id, HTTPStatus.NOT_FOUND).data is None


def test_delete_customer_reports_an_unknown_id(customers_service: CustomersService) -> None:
    response = customers_service.delete_customer(UNKNOWN_CUSTOMER_ID, HTTPStatus.NOT_FOUND)

    assert response.data is None
    assert response.error is not None
    assert response.error.code == ErrorCode.RESOURCE_MISSING
