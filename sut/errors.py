"""Error taxonomy and the responses that carry it."""

from enum import StrEnum
from http import HTTPStatus

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from sut.schemas import ErrorDetail

BODY_LOCATION = "body"
DICT_KEY_MARKER = "[key]"


class ErrorType(StrEnum):
    """Broad class of a failure, mirroring the status-code family."""

    CONFLICT = "conflict"
    INVALID_REQUEST = "invalid_request"
    NOT_FOUND = "not_found"


class ErrorCode(StrEnum):
    """The specific reason a request failed."""

    AMOUNT_TOO_SMALL = "amount_too_small"
    CUSTOMER_NOT_FOUND = "customer_not_found"
    CUSTOMER_REQUIRED = "customer_required"
    EMAIL_ALREADY_EXISTS = "email_already_exists"
    PARAMETER_INVALID = "parameter_invalid"
    PARAMETER_INVALID_ENUM = "parameter_invalid_enum"
    PARAMETER_INVALID_TYPE = "parameter_invalid_type"
    PARAMETER_MISSING = "parameter_missing"
    PARAMETER_OUT_OF_RANGE = "parameter_out_of_range"
    PARAMETER_UNKNOWN = "parameter_unknown"
    RESOURCE_MISSING = "resource_missing"


_EXACT_CODES = {
    "missing": ErrorCode.PARAMETER_MISSING,
    "extra_forbidden": ErrorCode.PARAMETER_UNKNOWN,
    "enum": ErrorCode.PARAMETER_INVALID_ENUM,
}
_RANGE_TYPES = frozenset(
    {
        "greater_than",
        "greater_than_equal",
        "less_than",
        "less_than_equal",
        "string_too_long",
        "string_too_short",
        "too_long",
        "too_short",
    },
)
_TYPE_MARKERS = ("_type", "_parsing", "_from_")


def error_response(
    status: HTTPStatus,
    error_type: ErrorType,
    code: ErrorCode,
    message: str,
    param: str | None = None,
) -> JSONResponse:
    """Build a response carrying an error envelope.

    Returns:
        A JSON response with data set to None and the error described.

    """
    detail = ErrorDetail(type=error_type, code=code, message=message, param=param)
    return JSONResponse(status_code=status, content={"data": None, "error": detail.model_dump()})


def not_found(resource: str, resource_id: str) -> JSONResponse:
    """Build a 404 response for a resource that does not exist.

    Returns:
        A JSON response carrying the not-found error envelope.

    """
    return error_response(
        HTTPStatus.NOT_FOUND,
        ErrorType.NOT_FOUND,
        ErrorCode.RESOURCE_MISSING,
        f"No such {resource}: {resource_id}",
        param="id",
    )


def invalid_request(code: ErrorCode, message: str, param: str) -> JSONResponse:
    """Build a 422 response for a request the service refuses to act on.

    Returns:
        A JSON response carrying the invalid-request error envelope.

    """
    return error_response(HTTPStatus.UNPROCESSABLE_ENTITY, ErrorType.INVALID_REQUEST, code, message, param)


def conflict(code: ErrorCode, message: str, param: str) -> JSONResponse:
    """Build a 409 response for a request that clashes with existing state.

    Returns:
        A JSON response carrying the conflict error envelope.

    """
    return error_response(HTTPStatus.CONFLICT, ErrorType.CONFLICT, code, message, param)


def validation_error_response(exc: RequestValidationError) -> JSONResponse:
    """Translate a Pydantic validation failure into the service's own taxonomy.

    Only the first failure is reported: a caller fixes one parameter at a time,
    and a single param keeps the error shape identical to every other error.

    Returns:
        A JSON response carrying the invalid-request error envelope.

    """
    failure = exc.errors()[0]
    location = failure["loc"]
    if location and location[0] == BODY_LOCATION:
        location = location[1:]
    location = tuple(part for part in location if part != DICT_KEY_MARKER)
    return invalid_request(
        _code_for(failure["type"]),
        failure["msg"],
        ".".join(str(part) for part in location),
    )


def _code_for(pydantic_type: str) -> ErrorCode:
    """Map a Pydantic error type onto this service's error code.

    A marker in the type name is enough to classify it: anything naming a type,
    a parsing failure or a conversion is the value not being what the parameter
    accepts.

    Returns:
        The matching error code, falling back to a generic invalid parameter.

    """
    if pydantic_type in _EXACT_CODES:
        return _EXACT_CODES[pydantic_type]
    if pydantic_type in _RANGE_TYPES:
        return ErrorCode.PARAMETER_OUT_OF_RANGE
    if any(marker in pydantic_type for marker in _TYPE_MARKERS):
        return ErrorCode.PARAMETER_INVALID_TYPE
    return ErrorCode.PARAMETER_INVALID
