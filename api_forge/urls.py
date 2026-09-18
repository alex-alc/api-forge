"""Endpoint paths for the API's resources."""

V1 = "/v1"

CUSTOMERS = f"{V1}/customers"
PAYMENT_INTENTS = f"{V1}/payment_intents"


def customer(customer_id: str) -> str:
    """Build the path addressing a single customer.

    Returns:
        The path for the given customer.

    """
    return f"{CUSTOMERS}/{customer_id}"


def payment_intent(payment_intent_id: str) -> str:
    """Build the path addressing a single payment intent.

    Returns:
        The path for the given payment intent.

    """
    return f"{PAYMENT_INTENTS}/{payment_intent_id}"
