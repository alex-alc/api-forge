"""Operational health endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Report that the service is up.

    Returns:
        A status payload.

    """
    return {"status": "ok"}
