"""Request payload factories, one set per resource.

A resource with optional fields gets a pair: a minimal factory carrying only
what the endpoint requires, and a full factory carrying every field it accepts.
Keyword arguments override individual values, so a test states only the field it
is about and inherits the rest.
"""

from faker import Faker

from api_forge.payment_intents import Currency, SetupFutureUsage

DEFAULT_AMOUNT_MINOR_UNITS = 2_000
DEFAULT_CURRENCY = Currency.USD
STATEMENT_DESCRIPTOR_SAMPLE = "ACME SUBSCRIPTION"


def customer(faker: Faker, **overrides: object) -> dict[str, object]:
    """Build a create-customer payload.

    The resource has no optional fields, so it needs no second factory.

    Returns:
        The payload, with any overrides applied.

    """
    return {"email": faker.unique.email(), "name": faker.name()} | overrides


def minimal_payment_intent(**overrides: object) -> dict[str, object]:
    """Build a create-payment-intent payload carrying only the required fields.

    Returns:
        The payload, with any overrides applied.

    """
    return {"amount": DEFAULT_AMOUNT_MINOR_UNITS, "currency": DEFAULT_CURRENCY} | overrides


def full_payment_intent(faker: Faker, customer_id: str, **overrides: object) -> dict[str, object]:
    """Build a create-payment-intent payload carrying every accepted field.

    Takes the customer explicitly because the API only accepts one that exists,
    and because setup_future_usage is refused without it.

    Returns:
        The payload, with any overrides applied.

    """
    return {
        "amount": DEFAULT_AMOUNT_MINOR_UNITS,
        "currency": DEFAULT_CURRENCY,
        "customer": customer_id,
        "description": faker.sentence(),
        "metadata": {"order_id": faker.uuid4()},
        "statement_descriptor": STATEMENT_DESCRIPTOR_SAMPLE,
        "setup_future_usage": SetupFutureUsage.OFF_SESSION,
    } | overrides
