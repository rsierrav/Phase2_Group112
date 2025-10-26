"""Artifact management endpoints."""

from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Query, Header, Response

from ..models import (
    Artifact,
    ArtifactMetadata,
    ArtifactQuery,
    ArtifactType,
    ArtifactID,
    EnumerateOffset,
)

router = APIRouter(
    prefix="/artifacts",
    tags=["artifacts"],
)


@router.post(
    "",
    response_model=list[ArtifactMetadata],
    responses={
        200: {"description": "List of artifacts"},
        400: {
            "description": "There is missing field(s) in the artifact_query or it is formed improperly, or is invalid."
        },
        413: {"description": "Too many artifacts returned."},
    },
)
async def artifacts_list(
    queries: list[ArtifactQuery],
    response: Response,
    offset: Annotated[
        EnumerateOffset | None, Query(description="Provide this for pagination")
    ] = None,
) -> list[ArtifactMetadata]:
    """
    Get the artifacts from the registry. (BASELINE)

    Search for artifacts satisfying the indicated query.
    If you want to enumerate all artifacts, provide an array with a single
    artifact_query whose name is "*".

    The response is paginated; the response header includes the offset to use in the next query.
    """
    # TODO: Implement artifact search logic
    # response.headers["offset"] = "next_offset_value"
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Endpoint not yet implemented"
    )


@router.get(
    "/{artifact_type}/{id}",
    response_model=Artifact,
    responses={
        200: {"description": "Return the artifact. url is required."},
        400: {
            "description": "There is missing field(s) in the artifact_type or artifact_id or it is formed improperly, or is invalid."
        },
        404: {"description": "Artifact does not exist."},
    },
)
async def artifact_retrieve(
    artifact_type: ArtifactType,
    id: ArtifactID,
) -> Artifact:
    """
    Interact with the artifact with this id. (BASELINE)

    Return this artifact.
    """
    # TODO: Implement artifact retrieval logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Endpoint not yet implemented"
    )


@router.put(
    "/{artifact_type}/{id}",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Artifact is updated."},
        400: {
            "description": "There is missing field(s) in the artifact_type or artifact_id or it is formed improperly, or is invalid."
        },
        404: {"description": "Artifact does not exist."},
    },
)
async def artifact_update(
    artifact_type: ArtifactType,
    id: ArtifactID,
    artifact: Artifact,
) -> dict[str, str]:
    """
    Update this content of the artifact. (BASELINE)

    The name and id must match.
    The artifact source (from artifact_data) will replace the previous contents.
    """
    # TODO: Implement artifact update logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Endpoint not yet implemented"
    )


@router.delete(
    "/{artifact_type}/{id}",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Artifact is deleted."},
        400: {
            "description": "There is missing field(s) in the artifact_type or artifact_id or invalid"
        },
        404: {"description": "Artifact does not exist."},
    },
)
async def artifact_delete(
    artifact_type: ArtifactType,
    id: ArtifactID,
) -> dict[str, str]:
    """
    Delete this artifact. (NON-BASELINE)

    Delete only the artifact that matches "id". (id is a unique identifier for an artifact)
    """
    # TODO: Implement artifact deletion logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Endpoint not yet implemented"
    )
