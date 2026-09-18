"""In-memory stores backing the service's resources."""

from sut.schemas import Customer, PaymentIntent

customers: dict[str, Customer] = {}
payment_intents: dict[str, PaymentIntent] = {}
