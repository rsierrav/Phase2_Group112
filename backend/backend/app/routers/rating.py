"""Model rating endpoints."""

from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Header

from ..models import (
    ModelRating,
    ArtifactID,
)

router = APIRouter(
    prefix="/artifact/model",
    tags=["rating"],
)


@router.get(
    "/{id}/rate",
    response_model=ModelRating,
    responses={
        200: {
            "description": "Return the rating. Only use this if each metric was computed successfully."
        },
        400: {
            "description": "There is missing field(s) in the artifact_id or it is formed improperly, or is invalid."
        },
        404: {"description": "Artifact does not exist."},
        500: {
            "description": "The artifact rating system encountered an error while computing at least one metric."
        },
    },
)
async def model_artifact_rate(
    id: ArtifactID,
) -> ModelRating:
    """
    Get ratings for this model artifact. (BASELINE)

    Return the rating. Only use this if each metric was computed successfully.
    """
    # TODO: Implement model rating logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Endpoint not yet implemented"
    )
