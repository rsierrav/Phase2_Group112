"""Artifact management endpoints."""

from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Query, Header, Response, Depends

from ..models import (
    Artifact,
    ArtifactData,
    ArtifactMetadata,
    ArtifactQuery,
    ArtifactType,
    ArtifactID,
    EnumerateOffset,
)
from ..dependencies import get_dynamodb_table
from ..utils.dynamodb import (
    query_artifacts_by_name,
    parse_pagination_token,
    encode_pagination_token,
    format_artifact_metadata,
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
        400: {"description": "Missing or invalid artifact_type or artifact_id."},
        413: {"description": "Too many artifacts returned."},
    },
)
async def artifacts_list(
    queries: list[ArtifactQuery],
    response: Response,
    x_authorization: Annotated[str | None, Header(alias="X-Authorization")] = None,
    offset: Annotated[
        EnumerateOffset | None, Query(description="Provide this for pagination")
    ] = None,
    table=Depends(get_dynamodb_table),
) -> list[ArtifactMetadata]:
    """
    Get the artifacts from the registry. (BASELINE)

    Baseline does not require auth; X-Authorization is ignored if present.
    """

    # Validate queries
    if not queries or len(queries) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one artifact query must be provided.",
        )

    # Parse pagination token
    last_evaluated_key = parse_pagination_token(offset)

    # Set a reasonable limit per page
    PAGE_SIZE = 100
    MAX_RESULTS = 1000

    all_artifacts: list[dict] = []
    next_key = last_evaluated_key

    try:
        # Process each query
        for query in queries:
            if not query.name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Artifact name is required in query.",
                )

            # Extract artifact types if provided
            artifact_types = None
            if query.types:
                artifact_types = [t.value for t in query.types]

            # Query DynamoDB
            items, next_key = query_artifacts_by_name(
                table=table,
                name=query.name,
                artifact_types=artifact_types,
                limit=PAGE_SIZE,
                last_evaluated_key=next_key,
            )

            # Add items to results
            all_artifacts.extend(items)

            # Check if we've hit the maximum result limit
            if len(all_artifacts) >= MAX_RESULTS:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Too many artifacts returned. Please refine your query or use pagination.",
                )

            # If we have a next key and haven't filled the page, continue
            # Otherwise, break to return current results
            if not next_key or len(all_artifacts) >= PAGE_SIZE:
                break

        # Format artifacts to match ArtifactMetadata schema
        formatted_artifacts = [
            ArtifactMetadata(**format_artifact_metadata(item)) for item in all_artifacts
        ]
        # Set pagination header if there are more results
        if next_key:
            next_offset = encode_pagination_token(next_key)
            if next_offset:
                response.headers["offset"] = next_offset

        return formatted_artifacts

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error and return 500
        print(f"Error querying artifacts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while querying artifacts.",
        )


@router.get(
    "/{artifact_type}/{id}",
    response_model=Artifact,
    responses={
        200: {"description": "Return the artifact. url is required."},
        400: {"description": "Missing or invalid artifact_type or artifact_id."},
        403: {
            "description": "Authentication failed due to invalid or missing AuthenticationToken."
        },
        404: {"description": "Artifact does not exist."},
        500: {"description": "The artifact storage encountered an error."},
    },
)
async def artifact_retrieve(
    artifact_type: ArtifactType,
    id: ArtifactID,
    x_authorization: Annotated[str | None, Header(alias="X-Authorization")] = None,
    table=Depends(get_dynamodb_table),
) -> Artifact:
    """
    Interact with the artifact with this id. (BASELINE)
    Baseline does not require auth; X-Authorization is ignored if present.
    """

    # Look up item in DynamoDB
    try:
        response = table.get_item(Key={"id": id})
    except Exception as e:  # noqa: BLE001
        print(f"Error retrieving artifact from DynamoDB: {e}")
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

    # Ensure the stored type matches the requested type
    if item.get("type") != artifact_type.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="artifact_type does not match stored artifact type.",
        )

    # Build metadata from stored item
    metadata = ArtifactMetadata(
        id=item["id"],
        name=item.get("name", "artifact"),
        type=artifact_type,
    )

    url = item.get("url")
    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Artifact is missing url in storage.",
        )

    data = ArtifactData(
        url=url,
        download_url=item.get("download_url", url),
    )

    return Artifact(metadata=metadata, data=data)


@router.put(
    "/{artifact_type}/{id}",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Artifact is updated."},
        400: {"description": "Missing or invalid artifact_type or artifact_id."},
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
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Endpoint not yet implemented"
    )


@router.delete(
    "/{artifact_type}/{id}",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Artifact is deleted."},
        400: {"description": "Missing or invalid artifact_type or artifact_id."},
        404: {"description": "Artifact does not exist."},
    },
)
async def artifact_delete(
    artifact_type: ArtifactType,
    id: ArtifactID,
    table=Depends(get_dynamodb_table),
) -> dict[str, str]:
    """
    Delete this artifact. (NON-BASELINE)

    Delete only the artifact that matches "id". (id is a unique identifier for an artifact)
    """
    # First check if artifact exists and type matches
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

    # Check type matches
    if item.get("type") != artifact_type.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="artifact_type does not match stored artifact type.",
        )

    # Delete the artifact
    try:
        table.delete_item(Key={"id": id})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The artifact storage encountered an error while deleting.",
        )

    return {"message": "Artifact deleted successfully"}
