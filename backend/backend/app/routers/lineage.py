"""Artifact lineage graph endpoints."""

from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Header

from ..models import (
    ArtifactLineageGraph,
    ArtifactID,
)

router = APIRouter(
    prefix="/artifact/model",
    tags=["lineage"],
)


@router.get(
    "/{id}/lineage",
    response_model=ArtifactLineageGraph,
    responses={
        200: {"description": "Lineage graph extracted from structured metadata."},
        400: {
            "description": "The lineage graph cannot be computed because the artifact metadata is missing or malformed."
        },
        404: {"description": "Artifact does not exist."},
    },
)
async def artifact_lineage_get(
    id: ArtifactID,
) -> ArtifactLineageGraph:
    """
    Retrieve the lineage graph for this artifact. (BASELINE)

    Lineage graph extracted from structured metadata.
    """
    # TODO: Implement lineage graph retrieval logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Endpoint not yet implemented"
    )
