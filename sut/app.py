"""FastAPI service used as the framework's system under test."""

from http import HTTPStatus
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from sut.schemas import CreateUserRequest, Envelope, User

app = FastAPI()


_users: dict[str, User] = {}


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the service is up.

    Returns:
        A status payload.

    """
    return {"status": "ok"}


@app.post("/users")
def create_user(request: CreateUserRequest) -> Envelope[User]:
    """Store a new user under a freshly generated id.

    Returns:
        The created user, wrapped in the response envelope.

    """
    user = User(id=str(uuid4()), email=request.email, name=request.name)
    _users[user.id] = user
    return Envelope[User](data=user)


@app.get("/users/{user_id}", response_model=Envelope[User])
def get_user(user_id: str) -> Envelope[User] | JSONResponse:
    """Look up a single user by id.

    Returns:
        The user wrapped in the response envelope, or a 404 error envelope.

    """
    user = _users.get(user_id)
    if user is None:
        return _not_found(user_id)
    return Envelope[User](data=user)


@app.delete("/users/{user_id}", response_model=Envelope[User])
def delete_user(user_id: str) -> Envelope[User] | JSONResponse:
    """Remove a user by id.

    Returns:
        An empty response envelope, or a 404 error envelope.

    """
    if _users.pop(user_id, None) is None:
        return _not_found(user_id)
    return Envelope[User]()


@app.exception_handler(RequestValidationError)
def handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return request-validation failures in the same envelope as every other response.

    Returns:
        A 422 response carrying the error envelope.

    """
    reasons = "; ".join(f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors())
    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content={"data": None, "error": reasons},
    )


def _not_found(user_id: str) -> JSONResponse:
    """Build a 404 response carrying the error envelope.

    Returns:
        A JSON response with the not-found envelope.

    """
    return JSONResponse(
        status_code=HTTPStatus.NOT_FOUND,
        content={"data": None, "error": f"user {user_id} not found"},
    )
