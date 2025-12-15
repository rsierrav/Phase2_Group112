"""Artifact lineage graph endpoints."""

from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Header, Depends

from ..models import (
    ArtifactLineageGraph,
    ArtifactLineageNode,
    ArtifactID,
)
from ..dependencies import get_dynamodb_table

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
            "description": "The lineage graph cannot be computed because the "
            "artifact metadata is missing or malformed."
        },
        404: {"description": "Artifact does not exist."},
    },
)
async def artifact_lineage_get(
    id: ArtifactID,
    x_authorization: Annotated[str | None, Header(alias="X-Authorization")] = None,
    table=Depends(get_dynamodb_table),
) -> ArtifactLineageGraph:
    """
    Retrieve the lineage graph for this artifact. (BASELINE)

    Lineage graph extracted from structured metadata.
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

    name = item.get("name", "unknown")

    nodes = [ArtifactLineageNode(artifact_id=id, name=name, source="config_json", metadata={})]

    edges = []

    return ArtifactLineageGraph(nodes=nodes, edges=edges)
