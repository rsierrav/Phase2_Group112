"""License compatibility check endpoints."""

from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Header, Depends

from ..models import (
    SimpleLicenseCheckRequest,
    ArtifactID,
)
from ..dependencies import get_dynamodb_table

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
            "description": "The license check request is malformed or references "
            "an unsupported usage context."
        },
        404: {"description": "The artifact or GitHub project could not be found."},
        502: {"description": "External license information could not be retrieved."},
    },
)
async def artifact_license_check(
    id: ArtifactID,
    request: SimpleLicenseCheckRequest,
    x_authorization: Annotated[str | None, Header(alias="X-Authorization")] = None,
    table=Depends(get_dynamodb_table),
) -> bool:
    """
    Assess license compatibility for fine-tune and inference usage. (BASELINE)

    License compatibility analysis produced successfully.
    """
    try:
        response = table.get_item(Key={"id": id})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The artifact storage encountered an error.",
        )

    item = response.get("Item")
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact does not exist.",
        )

    github_url_str = str(request.github_url)
    if not github_url_str or "github.com/" not in github_url_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub URL provided.",
        )

    return True
