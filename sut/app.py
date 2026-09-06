"""FastAPI service used as the framework's system under test."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the service is up.

    Returns:
        A status payload.

    """
    return {"status": "ok"}
