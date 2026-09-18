"""Payment intent endpoints."""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from sut import storage
from sut.errors import ErrorCode, invalid_request, not_found
from sut.schemas import (
    MINIMUM_CHARGE_MINOR_UNITS,
    CreatePaymentIntentRequest,
    Envelope,
    PaymentIntent,
    PaymentIntentStatus,
)

PAYMENT_INTENT_ID_PREFIX = "pi_"
RESOURCE = "payment_intent"

router = APIRouter(tags=["payment_intents"])


@router.post("/payment_intents", response_model=Envelope[PaymentIntent])
def create_payment_intent(request: CreatePaymentIntentRequest) -> Envelope[PaymentIntent] | JSONResponse:
    """Create an intent to collect a payment.

    Returns:
        The created intent wrapped in the response envelope, or a 422 error
        envelope when the request violates a rule spanning several fields.

    """
    if request.setup_future_usage is not None and request.customer is None:
        return invalid_request(
            ErrorCode.CUSTOMER_REQUIRED,
            "setup_future_usage requires a customer to attach the payment method to",
            "customer",
        )
    if request.customer is not None and request.customer not in storage.customers:
        return invalid_request(
            ErrorCode.CUSTOMER_NOT_FOUND,
            f"No such customer: {request.customer}",
            "customer",
        )
    minimum = MINIMUM_CHARGE_MINOR_UNITS[request.currency]
    if request.amount < minimum:
        return invalid_request(
            ErrorCode.AMOUNT_TOO_SMALL,
            f"Amount must be at least {minimum} for {request.currency}",
            "amount",
        )

    intent = PaymentIntent(
        id=f"{PAYMENT_INTENT_ID_PREFIX}{uuid4().hex}",
        status=PaymentIntentStatus.REQUIRES_PAYMENT,
        amount=request.amount,
        currency=request.currency,
        customer=request.customer,
        description=request.description,
        metadata=request.metadata,
        statement_descriptor=request.statement_descriptor,
        setup_future_usage=request.setup_future_usage,
        created_at=datetime.now(tz=UTC),
    )
    storage.payment_intents[intent.id] = intent
    return Envelope[PaymentIntent](data=intent)


@router.get("/payment_intents/{payment_intent_id}", response_model=Envelope[PaymentIntent])
def get_payment_intent(payment_intent_id: str) -> Envelope[PaymentIntent] | JSONResponse:
    """Look up a single payment intent by id.

    Returns:
        The intent wrapped in the response envelope, or a 404 error envelope.

    """
    intent = storage.payment_intents.get(payment_intent_id)
    if intent is None:
        return not_found(RESOURCE, payment_intent_id)
    return Envelope[PaymentIntent](data=intent)
