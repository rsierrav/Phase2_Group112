"""Artifact creation (ingestion) endpoints."""

from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Header

from ..models import (
    Artifact,
    ArtifactData,
    ArtifactType,
)

router = APIRouter(
    prefix="/artifact",
    tags=["artifact"],
)


@router.post(
    "/{artifact_type}",
    status_code=status.HTTP_201_CREATED,
    response_model=Artifact,
    responses={
        201: {"description": "Success. Check the id in the returned metadata for the official ID."},
        202: {
            "description": "Artifact ingest accepted but the rating pipeline deferred the evaluation. Use this when the package is stored but rating is performed asynchronously and the artifact is dropped silently if the rating later fails. Subsequent requests to `/rate` or any other endpoint with this artifact id should return 404 until a rating result exists."
        },
        400: {
            "description": "There is missing field(s) in the artifact_data or it is formed improperly (must include a single url)."
        },
        409: {"description": "Artifact exists already."},
        424: {"description": "Artifact is not registered due to the disqualified rating."},
    },
)
async def artifact_create(
    artifact_type: ArtifactType,
    artifact_data: ArtifactData,
) -> Artifact:
    """
    Register a new artifact. (BASELINE)

    Register a new artifact by providing a downloadable source url.
    Artifacts may share a name with existing entries; refer to the description
    above to see how an id is formed for an artifact.
    """
    # TODO: Implement artifact creation logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Endpoint not yet implemented"
    )
