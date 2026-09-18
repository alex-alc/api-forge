"""FastAPI service used as the framework's system under test."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from sut.errors import validation_error_response
from sut.routers import customers, health, payment_intents

API_PREFIX = "/v1"

app = FastAPI(title="api-forge payments SUT")

app.include_router(health.router)
app.include_router(customers.router, prefix=API_PREFIX)
app.include_router(payment_intents.router, prefix=API_PREFIX)


@app.exception_handler(RequestValidationError)
def handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return request-validation failures in the same envelope as every other response.

    Returns:
        A 422 response carrying the error envelope.

    """
    return validation_error_response(exc)
