from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "invix-backend"


@router.get("", response_model=HealthResponse)
def health() -> HealthResponse:
    """Check that the API process is responding."""
    return HealthResponse()
