"""Service client for the payment intent endpoints."""

from datetime import datetime
from enum import StrEnum
from http import HTTPStatus

from pydantic import BaseModel, Field

from api_forge import urls
from api_forge.response import ApiResponse
from api_forge.service import BaseService

PAYMENT_INTENT_ID_PREFIX = "pi_"

# Limits the API documents and enforces; stated here so tests assert against
# their own copy rather than importing the service's.
AMOUNT_MAX_MINOR_UNITS = 99_999_999
DESCRIPTION_MAX_LENGTH = 350
METADATA_KEY_MAX_LENGTH = 40
METADATA_MAX_KEYS = 50
METADATA_VALUE_MAX_LENGTH = 500
STATEMENT_DESCRIPTOR_MAX_LENGTH = 22


class Currency(StrEnum):
    """Currencies the API settles in."""

    EUR = "eur"
    GBP = "gbp"
    USD = "usd"


MINIMUM_CHARGE_MINOR_UNITS = {
    Currency.EUR: 40,
    Currency.GBP: 30,
    Currency.USD: 50,
}


class PaymentIntentStatus(StrEnum):
    """States a payment intent moves through."""

    CANCELED = "canceled"
    FAILED = "failed"
    PROCESSING = "processing"
    REQUIRES_PAYMENT = "requires_payment"
    SUCCEEDED = "succeeded"


class SetupFutureUsage(StrEnum):
    """Declared intent to reuse the payment method after this payment."""

    OFF_SESSION = "off_session"
    ON_SESSION = "on_session"


class PaymentIntent(BaseModel):
    """A payment intent as returned by the API.

    Attributes:
        id: Server-assigned identifier.
        status: Where the intent sits in its lifecycle.
        amount: Amount to collect, in the currency's minor units.
        currency: Currency to collect in.
        customer: The paying customer, absent for a guest payment.
        description: Internal note about the payment.
        metadata: Arbitrary key-value pairs supplied on creation.
        statement_descriptor: What the payer sees on their statement.
        setup_future_usage: Declared intent to reuse the payment method.
        created_at: When the intent was created.

    """

    id: str
    status: str
    amount: int
    currency: str
    customer: str | None = None
    description: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    statement_descriptor: str | None = None
    setup_future_usage: str | None = None
    created_at: datetime


class PaymentIntentsService(BaseService):
    """Calls the payment intent endpoints.

    Every operation takes the status code the caller expects, defaulting to the
    happy path, and returns the parsed response envelope. Positive and negative
    cases therefore share one code path.
    """

    def create_payment_intent(
        self,
        payload: object,
        expected_status: HTTPStatus = HTTPStatus.OK,
    ) -> ApiResponse[PaymentIntent]:
        """Create a payment intent from any payload.

        Returns:
            The parsed response envelope.

        """
        response = self._client.post(urls.PAYMENT_INTENTS, json=payload)
        return self._envelope(response, PaymentIntent, expected_status)

    def get_payment_intent(
        self,
        payment_intent_id: str,
        expected_status: HTTPStatus = HTTPStatus.OK,
    ) -> ApiResponse[PaymentIntent]:
        """Fetch a single payment intent by id.

        Returns:
            The parsed response envelope.

        """
        response = self._client.get(urls.payment_intent(payment_intent_id))
        return self._envelope(response, PaymentIntent, expected_status)
