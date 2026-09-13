"""Request and response models for the system under test."""

from pydantic import BaseModel, EmailStr


class CreateUserRequest(BaseModel):
    """Payload accepted by the create-user endpoint.

    Attributes:
        email: The user's email address.
        name: The user's display name.

    """

    email: EmailStr
    name: str


class User(BaseModel):
    """A stored user.

    Attributes:
        id: Server-assigned identifier.
        email: The user's email address.
        name: The user's display name.

    """

    id: str
    email: EmailStr
    name: str


class Envelope[DataT](BaseModel):
    """Envelope wrapping a response payload or the error that replaced it.

    Attributes:
        data: The payload, or None when the call failed or returned nothing.
        error: Error message, or None when the call succeeded.

    """

    data: DataT | None = None
    error: str | None = None
