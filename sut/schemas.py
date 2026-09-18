"""Request and response models for the system under test."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

AMOUNT_MAX_MINOR_UNITS = 99_999_999
DESCRIPTION_MAX_LENGTH = 350
METADATA_KEY_MAX_LENGTH = 40
METADATA_MAX_KEYS = 50
METADATA_VALUE_MAX_LENGTH = 500
STATEMENT_DESCRIPTOR_MAX_LENGTH = 22

MetadataKey = Annotated[str, StringConstraints(max_length=METADATA_KEY_MAX_LENGTH)]
MetadataValue = Annotated[str, StringConstraints(max_length=METADATA_VALUE_MAX_LENGTH)]


class Currency(StrEnum):
    """Currencies the service settles in."""

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


class ErrorDetail(BaseModel):
    """Machine-readable description of a failed request.

    Attributes:
        type: Broad class of the failure.
        code: The specific reason, stable enough for a client to branch on.
        message: Human-readable explanation.
        param: The offending field, when the failure is field-level.

    """

    type: str
    code: str
    message: str
    param: str | None = None


class Envelope[DataT](BaseModel):
    """Envelope wrapping a response payload or the error that replaced it.

    Attributes:
        data: The payload, or None when the call failed or returned nothing.
        error: Error details, or None when the call succeeded.

    """

    data: DataT | None = None
    error: ErrorDetail | None = None


class CreateCustomerRequest(BaseModel):
    """Payload accepted by the create-customer endpoint.

    Attributes:
        email: The customer's email address.
        name: The customer's display name.

    """

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    name: str

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        """Lower-case the whole address, which makes it usable as an identifier.

        EmailStr already lower-cases the domain; the local part is what is left.

        Returns:
            The normalized address.

        """
        return value.lower()


class Customer(BaseModel):
    """A stored customer — the payer a payment intent refers to.

    Attributes:
        id: Server-assigned identifier.
        email: The customer's email address.
        name: The customer's display name.
        created_at: When the customer was created.

    """

    id: str
    email: EmailStr
    name: str
    created_at: datetime


class CreatePaymentIntentRequest(BaseModel):
    """Payload accepted by the create-payment-intent endpoint.

    Attributes:
        amount: Amount to collect, in the currency's minor units.
        currency: Currency to collect in.
        customer: The paying customer, absent for a guest payment.
        description: Internal note about the payment.
        metadata: Arbitrary key-value pairs echoed back on the intent.
        statement_descriptor: What the payer sees on their statement.
        setup_future_usage: Declares the payment method will be reused, which
            requires a customer to attach it to.

    """

    model_config = ConfigDict(extra="forbid")

    # strict: a money field never coerces. Lax mode would read "2000" as 2000
    # and true as 1, turning a malformed request into a silent charge.
    amount: int = Field(gt=0, le=AMOUNT_MAX_MINOR_UNITS, strict=True)
    currency: Currency
    customer: str | None = None
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    metadata: dict[MetadataKey, MetadataValue] = Field(default_factory=dict, max_length=METADATA_MAX_KEYS)
    statement_descriptor: str | None = Field(default=None, max_length=STATEMENT_DESCRIPTOR_MAX_LENGTH)
    setup_future_usage: SetupFutureUsage | None = None


class PaymentIntent(BaseModel):
    """An intent to collect a payment.

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
    status: PaymentIntentStatus
    amount: int
    currency: Currency
    customer: str | None = None
    description: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    statement_descriptor: str | None = None
    setup_future_usage: SetupFutureUsage | None = None
    created_at: datetime
