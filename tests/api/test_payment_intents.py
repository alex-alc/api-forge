"""Tests for the SUT's payment intent endpoints."""

from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from faker import Faker

from api_forge import data
from api_forge.customers import CustomersService
from api_forge.payment_intents import (
    AMOUNT_MAX_MINOR_UNITS,
    DESCRIPTION_MAX_LENGTH,
    METADATA_KEY_MAX_LENGTH,
    METADATA_MAX_KEYS,
    METADATA_VALUE_MAX_LENGTH,
    MINIMUM_CHARGE_MINOR_UNITS,
    PAYMENT_INTENT_ID_PREFIX,
    STATEMENT_DESCRIPTOR_MAX_LENGTH,
    Currency,
    PaymentIntentsService,
    PaymentIntentStatus,
    SetupFutureUsage,
)
from api_forge.response import ErrorCode, ErrorType

if TYPE_CHECKING:
    from collections.abc import Callable

    from api_forge.customers import Customer

UNKNOWN_CUSTOMER_ID = "cus_00000000000000000000000000000000"
UNKNOWN_PAYMENT_INTENT_ID = "pi_00000000000000000000000000000000"

CUSTOMER_EXISTING = "existing"
CUSTOMER_DELETED = "deleted"
CUSTOMER_NEVER_EXISTED = "never_existed"

CURRENCY_IDS = [currency.value for currency in Currency]
OVERSIZED_METADATA_KEY = "k" * (METADATA_KEY_MAX_LENGTH + 1)


def _without(field: str) -> dict[str, object]:
    payload = data.minimal_payment_intent()
    del payload[field]
    return payload


@pytest.fixture
def customer_reference(
    request: pytest.FixtureRequest,
    customers_service: CustomersService,
    make_customer: "Callable[..., Customer]",
) -> str:
    """Provide a customer id in the state the test asked for.

    Driven indirectly: the test names a state and receives an id, so the setup
    each state needs stays out of the test body.

    Returns:
        The id of a customer that exists, was deleted, or never existed at all.

    """
    if request.param == CUSTOMER_NEVER_EXISTED:
        return UNKNOWN_CUSTOMER_ID
    customer = make_customer()
    if request.param == CUSTOMER_DELETED:
        customers_service.delete_customer(customer.id)
    return customer.id


def test_create_payment_intent_with_required_fields_only(
    payment_intents_service: PaymentIntentsService,
) -> None:
    payload = data.minimal_payment_intent()

    response = payment_intents_service.create_payment_intent(payload)

    assert response.error is None
    intent = response.data
    assert intent is not None
    assert intent.id.startswith(PAYMENT_INTENT_ID_PREFIX)
    assert intent.status == PaymentIntentStatus.REQUIRES_PAYMENT
    assert intent.amount == payload["amount"]
    assert intent.currency == payload["currency"]
    assert intent.customer is None
    assert intent.description is None
    assert intent.metadata == {}
    assert intent.statement_descriptor is None
    assert intent.setup_future_usage is None


@pytest.mark.parametrize("customer_reference", [CUSTOMER_EXISTING], indirect=True)
def test_create_payment_intent_with_every_field(
    payment_intents_service: PaymentIntentsService,
    customer_reference: str,
    faker: Faker,
) -> None:
    payload = data.full_payment_intent(faker, customer_reference)

    response = payment_intents_service.create_payment_intent(payload)

    assert response.error is None
    intent = response.data
    assert intent is not None
    assert intent.customer == customer_reference
    assert intent.description == payload["description"]
    assert intent.metadata == payload["metadata"]
    assert intent.statement_descriptor == payload["statement_descriptor"]
    assert intent.setup_future_usage == SetupFutureUsage.OFF_SESSION


@pytest.mark.parametrize(
    ("payload", "expected_code", "expected_param"),
    [
        pytest.param(_without("amount"), ErrorCode.PARAMETER_MISSING, "amount", id="missing_amount"),
        pytest.param(_without("currency"), ErrorCode.PARAMETER_MISSING, "currency", id="missing_currency"),
        pytest.param({}, ErrorCode.PARAMETER_MISSING, "amount", id="empty_payload"),
        pytest.param(
            data.minimal_payment_intent(amount=0),
            ErrorCode.PARAMETER_OUT_OF_RANGE,
            "amount",
            id="amount_zero",
        ),
        pytest.param(
            data.minimal_payment_intent(amount=AMOUNT_MAX_MINOR_UNITS + 1),
            ErrorCode.PARAMETER_OUT_OF_RANGE,
            "amount",
            id="amount_above_maximum",
        ),
        pytest.param(
            data.minimal_payment_intent(amount=[]),
            ErrorCode.PARAMETER_INVALID_TYPE,
            "amount",
            id="amount_not_a_number",
        ),
        pytest.param(
            data.minimal_payment_intent(amount="not-a-number"),
            ErrorCode.PARAMETER_INVALID_TYPE,
            "amount",
            id="amount_unparsable_string",
        ),
        pytest.param(
            data.minimal_payment_intent(amount="2000"),
            ErrorCode.PARAMETER_INVALID_TYPE,
            "amount",
            id="amount_numeric_string",
        ),
        pytest.param(
            data.minimal_payment_intent(amount=True),
            ErrorCode.PARAMETER_INVALID_TYPE,
            "amount",
            id="amount_boolean",
        ),
        pytest.param(
            data.minimal_payment_intent(amount=2000.0),
            ErrorCode.PARAMETER_INVALID_TYPE,
            "amount",
            id="amount_float",
        ),
        pytest.param(
            data.minimal_payment_intent(currency="chf"),
            ErrorCode.PARAMETER_INVALID_ENUM,
            "currency",
            id="unsupported_currency",
        ),
        pytest.param(
            data.minimal_payment_intent(description="x" * (DESCRIPTION_MAX_LENGTH + 1)),
            ErrorCode.PARAMETER_OUT_OF_RANGE,
            "description",
            id="description_too_long",
        ),
        pytest.param(
            data.minimal_payment_intent(statement_descriptor="x" * (STATEMENT_DESCRIPTOR_MAX_LENGTH + 1)),
            ErrorCode.PARAMETER_OUT_OF_RANGE,
            "statement_descriptor",
            id="statement_descriptor_too_long",
        ),
        pytest.param(
            data.minimal_payment_intent(metadata={f"k{index}": "v" for index in range(METADATA_MAX_KEYS + 1)}),
            ErrorCode.PARAMETER_OUT_OF_RANGE,
            "metadata",
            id="too_many_metadata_keys",
        ),
        pytest.param(
            data.minimal_payment_intent(metadata={OVERSIZED_METADATA_KEY: "v"}),
            ErrorCode.PARAMETER_OUT_OF_RANGE,
            f"metadata.{OVERSIZED_METADATA_KEY}",
            id="metadata_key_too_long",
        ),
        pytest.param(
            data.minimal_payment_intent(metadata={"note": "v" * (METADATA_VALUE_MAX_LENGTH + 1)}),
            ErrorCode.PARAMETER_OUT_OF_RANGE,
            "metadata.note",
            id="metadata_value_too_long",
        ),
        pytest.param(
            data.minimal_payment_intent(nickname="adz"),
            ErrorCode.PARAMETER_UNKNOWN,
            "nickname",
            id="unknown_field",
        ),
        pytest.param(
            data.minimal_payment_intent(statement_descriptor='ACME "SUB"'),
            ErrorCode.PARAMETER_INVALID,
            "statement_descriptor",
            id="statement_descriptor_with_forbidden_characters",
            marks=pytest.mark.xfail(
                reason="the SUT does not yet reject <, >, backslash and quotes in statement_descriptor",
                strict=True,
            ),
        ),
    ],
)
def test_create_payment_intent_rejects_an_invalid_payload(
    payment_intents_service: PaymentIntentsService,
    payload: dict[str, object],
    expected_code: ErrorCode,
    expected_param: str,
) -> None:
    response = payment_intents_service.create_payment_intent(payload, HTTPStatus.UNPROCESSABLE_ENTITY)

    assert response.data is None
    assert response.error is not None
    assert response.error.type == ErrorType.INVALID_REQUEST
    assert response.error.code == expected_code
    assert response.error.param == expected_param


@pytest.mark.parametrize("currency", list(Currency), ids=CURRENCY_IDS)
def test_amount_below_the_currency_minimum_is_rejected(
    payment_intents_service: PaymentIntentsService,
    currency: Currency,
) -> None:
    minimum = MINIMUM_CHARGE_MINOR_UNITS[currency]
    payload = data.minimal_payment_intent(amount=minimum - 1, currency=currency)

    response = payment_intents_service.create_payment_intent(payload, HTTPStatus.UNPROCESSABLE_ENTITY)

    assert response.data is None
    assert response.error is not None
    assert response.error.code == ErrorCode.AMOUNT_TOO_SMALL
    assert response.error.param == "amount"
    assert str(minimum) in response.error.message


@pytest.mark.parametrize("offset", [0, 1], ids=["at_minimum", "above_minimum"])
@pytest.mark.parametrize("currency", list(Currency), ids=CURRENCY_IDS)
def test_amount_at_or_above_the_currency_minimum_is_accepted(
    payment_intents_service: PaymentIntentsService,
    currency: Currency,
    offset: int,
) -> None:
    amount = MINIMUM_CHARGE_MINOR_UNITS[currency] + offset

    response = payment_intents_service.create_payment_intent(
        data.minimal_payment_intent(amount=amount, currency=currency),
    )

    assert response.error is None
    assert response.data is not None
    assert response.data.amount == amount
    assert response.data.currency == currency


def test_the_minimum_charge_is_per_currency_not_global(
    payment_intents_service: PaymentIntentsService,
) -> None:
    cheapest = min(MINIMUM_CHARGE_MINOR_UNITS, key=lambda currency: MINIMUM_CHARGE_MINOR_UNITS[currency])
    priciest = max(MINIMUM_CHARGE_MINOR_UNITS, key=lambda currency: MINIMUM_CHARGE_MINOR_UNITS[currency])
    amount = MINIMUM_CHARGE_MINOR_UNITS[priciest] - 1

    accepted = payment_intents_service.create_payment_intent(
        data.minimal_payment_intent(amount=amount, currency=cheapest),
    )
    rejected = payment_intents_service.create_payment_intent(
        data.minimal_payment_intent(amount=amount, currency=priciest),
        HTTPStatus.UNPROCESSABLE_ENTITY,
    )

    assert accepted.data is not None
    assert accepted.data.amount == amount
    assert rejected.error is not None
    assert rejected.error.code == ErrorCode.AMOUNT_TOO_SMALL


def test_create_payment_intent_requires_a_customer_to_reuse_the_payment_method(
    payment_intents_service: PaymentIntentsService,
) -> None:
    payload = data.minimal_payment_intent(setup_future_usage=SetupFutureUsage.OFF_SESSION)

    response = payment_intents_service.create_payment_intent(payload, HTTPStatus.UNPROCESSABLE_ENTITY)

    assert response.data is None
    assert response.error is not None
    assert response.error.type == ErrorType.INVALID_REQUEST
    assert response.error.code == ErrorCode.CUSTOMER_REQUIRED
    assert response.error.param == "customer"


@pytest.mark.parametrize(
    "customer_reference",
    [CUSTOMER_DELETED, CUSTOMER_NEVER_EXISTED],
    indirect=True,
)
def test_create_payment_intent_rejects_a_customer_that_is_not_there(
    payment_intents_service: PaymentIntentsService,
    customer_reference: str,
) -> None:
    payload = data.minimal_payment_intent(customer=customer_reference)

    response = payment_intents_service.create_payment_intent(payload, HTTPStatus.UNPROCESSABLE_ENTITY)

    assert response.data is None
    assert response.error is not None
    assert response.error.code == ErrorCode.CUSTOMER_NOT_FOUND
    assert response.error.param == "customer"


def test_get_payment_intent_returns_the_stored_intent(
    payment_intents_service: PaymentIntentsService,
) -> None:
    created = payment_intents_service.create_payment_intent(data.minimal_payment_intent()).data
    assert created is not None

    response = payment_intents_service.get_payment_intent(created.id)

    assert response.error is None
    assert response.data == created


def test_get_payment_intent_reports_an_unknown_id(
    payment_intents_service: PaymentIntentsService,
) -> None:
    response = payment_intents_service.get_payment_intent(UNKNOWN_PAYMENT_INTENT_ID, HTTPStatus.NOT_FOUND)

    assert response.data is None
    assert response.error is not None
    assert response.error.type == ErrorType.NOT_FOUND
    assert response.error.code == ErrorCode.RESOURCE_MISSING
