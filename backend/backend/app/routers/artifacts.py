"""Artifact management endpoints."""

import json
import base64
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Query, Header, Response, Depends

from ..models import (
    Artifact,
    ArtifactMetadata,
    ArtifactQuery,
    ArtifactType,
    ArtifactID,
    EnumerateOffset,
)
from ..db.dynamodb import DynamoDBService, get_db_service
from ..config import Settings, get_settings

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
    db: DynamoDBService = Depends(get_db_service),
    settings: Settings = Depends(get_settings),
) -> list[ArtifactMetadata]:
    """
    Get the artifacts from the registry. (BASELINE)

    Search for artifacts satisfying the indicated query.
    If you want to enumerate all artifacts, provide an array with a single
    artifact_query whose name is "*".

    The response is paginated; the response header includes the offset to use in the next query.
    """
    if not queries:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="At least one query is required"
        )

    # Decode pagination token if provided
    last_evaluated_key = None
    if offset:
        try:
            last_evaluated_key = json.loads(base64.b64decode(offset))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid offset token"
            )

    # Set pagination limit
    limit = settings.DEFAULT_PAGE_SIZE

    # Handle the special case of enumerate all (name = "*")
    if len(queries) == 1 and queries[0].name == "*":
        artifacts, next_key = await db.scan_all_artifacts(
            limit=limit, last_evaluated_key=last_evaluated_key
        )
    else:
        # TODO: This is probably slow for multiple queries; see what we can do to optimize
        all_artifacts = []
        next_key = None

        for query in queries:
            artifacts, next_key = await db.query_artifacts_by_name(
                name=query.name,
                artifact_types=query.types,
                limit=limit,
                last_evaluated_key=last_evaluated_key,
            )
            all_artifacts.extend(artifacts)

            # Limit total results
            if len(all_artifacts) >= limit:
                all_artifacts = all_artifacts[:limit]
                break

        artifacts = all_artifacts

    # TODO: Does the "offset" *need* to be a page number?
    # This uses the next key from DynamoDB directly as the offset.
    # If we need the offset to be a page number, we need to fix this.
    if next_key:
        offset_token = base64.b64encode(json.dumps(next_key).encode()).decode()
        print(f"next_key: {next_key}, offset_token: {offset_token}")
        response.headers["offset"] = offset_token

    return artifacts


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
