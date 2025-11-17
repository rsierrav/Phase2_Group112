"""Artifact cost calculation endpoints."""

from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Query, Header

from ..models import (
    ArtifactCost,
    ArtifactType,
    ArtifactID,
)

router = APIRouter(
    prefix="/artifact",
    tags=["cost"],
)


@router.get(
    "/{artifact_type}/{id}/cost",
    response_model=ArtifactCost,
    responses={
        200: {"description": "Return the total cost of the artifact, and its dependencies"},
        400: {
            "description": "There is missing field(s) in the artifact_type or artifact_id or it is formed improperly, or is invalid."
        },
        404: {"description": "Artifact does not exist."},
        500: {"description": "The artifact cost calculator encountered an error."},
    },
)
async def artifact_cost(
    artifact_type: ArtifactType,
    id: ArtifactID,
    dependency: Annotated[
        bool, Query(description="Include dependencies in cost calculation")
    ] = False,
) -> ArtifactCost:
    """
    Get the cost of an artifact (BASELINE)

    Return the total cost of the artifact, and its dependencies
    """
    # TODO: Implement artifact cost calculation logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Endpoint not yet implemented"
    )
