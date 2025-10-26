"""License compatibility check endpoints."""

from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Header

from ..models import (
    SimpleLicenseCheckRequest,
    ArtifactID,
)

router = APIRouter(
    prefix="/artifact/model",
    tags=["license"],
)


@router.post(
    "/{id}/license-check",
    response_model=bool,
    responses={
        200: {"description": "License compatibility analysis produced successfully."},
        400: {
            "description": "The license check request is malformed or references an unsupported usage context."
        },
        404: {"description": "The artifact or GitHub project could not be found."},
        502: {"description": "External license information could not be retrieved."},
    },
)
async def artifact_license_check(
    id: ArtifactID,
    request: SimpleLicenseCheckRequest,
) -> bool:
    """
    Assess license compatibility for fine-tune and inference usage. (BASELINE)

    License compatibility analysis produced successfully.
    """
    # TODO: Implement license compatibility check logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Endpoint not yet implemented"
    )
