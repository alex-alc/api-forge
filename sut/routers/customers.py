"""Customer endpoints."""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from sut import storage
from sut.errors import ErrorCode, conflict, not_found
from sut.schemas import CreateCustomerRequest, Customer, Envelope

CUSTOMER_ID_PREFIX = "cus_"
RESOURCE = "customer"

router = APIRouter(tags=["customers"])


@router.post("/customers", response_model=Envelope[Customer])
def create_customer(request: CreateCustomerRequest) -> Envelope[Customer] | JSONResponse:
    """Store a new customer under a freshly generated id.

    The email identifies the customer, so an address already in use is refused
    rather than producing a second record for the same person.

    Returns:
        The created customer wrapped in the response envelope, or a 409 error
        envelope when the email is taken.

    """
    if any(existing.email == request.email for existing in storage.customers.values()):
        return conflict(
            ErrorCode.EMAIL_ALREADY_EXISTS,
            f"A customer with email {request.email} already exists",
            "email",
        )

    customer = Customer(
        id=f"{CUSTOMER_ID_PREFIX}{uuid4().hex}",
        email=request.email,
        name=request.name,
        created_at=datetime.now(tz=UTC),
    )
    storage.customers[customer.id] = customer
    return Envelope[Customer](data=customer)


@router.get("/customers/{customer_id}", response_model=Envelope[Customer])
def get_customer(customer_id: str) -> Envelope[Customer] | JSONResponse:
    """Look up a single customer by id.

    Returns:
        The customer wrapped in the response envelope, or a 404 error envelope.

    """
    customer = storage.customers.get(customer_id)
    if customer is None:
        return not_found(RESOURCE, customer_id)
    return Envelope[Customer](data=customer)


@router.delete("/customers/{customer_id}", response_model=Envelope[Customer])
def delete_customer(customer_id: str) -> Envelope[Customer] | JSONResponse:
    """Remove a customer by id.

    Returns:
        An empty response envelope, or a 404 error envelope.

    """
    if storage.customers.pop(customer_id, None) is None:
        return not_found(RESOURCE, customer_id)
    return Envelope[Customer]()
