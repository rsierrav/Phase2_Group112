"""Artifact search endpoints."""

from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Header

from ..models import (
    ArtifactMetadata,
    ArtifactName,
    ArtifactRegEx,
)

router = APIRouter(
    prefix="/artifact",
    tags=["search"],
)


@router.get(
    "/byName/{name}",
    response_model=list[ArtifactMetadata],
    responses={
        200: {"description": "Return artifact metadata entries that match the provided name."},
        400: {
            "description": "There is missing field(s) in the artifact_name or it is formed improperly, or is invalid."
        },
        404: {"description": "No such artifact."},
    },
)
async def artifact_by_name_get(
    name: ArtifactName,
) -> list[ArtifactMetadata]:
    """
    List artifact metadata for this name. (NON-BASELINE)

    Return metadata for each artifact matching this name.
    """
    # TODO: Implement search by name logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Endpoint not yet implemented"
    )


@router.post(
    "/byRegEx",
    response_model=list[ArtifactMetadata],
    responses={
        200: {"description": "Return a list of artifacts."},
        400: {
            "description": "There is missing field(s) in the artifact_regex or it is formed improperly, or is invalid"
        },
        404: {"description": "No artifact found under this regex."},
    },
)
async def artifact_by_regex_get(
    regex_query: ArtifactRegEx,
) -> list[ArtifactMetadata]:
    """
    Get any artifacts fitting the regular expression (BASELINE).

    Search for an artifact using regular expression over artifact names
    and READMEs. This is similar to search by name.
    """
    # TODO: Implement regex search logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Endpoint not yet implemented"
    )
