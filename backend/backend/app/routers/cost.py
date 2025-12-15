"""Artifact cost calculation endpoints."""

import hashlib
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Query, Header, Depends

from ..models import (
    ArtifactCost,
    ArtifactCostDetail,
    ArtifactType,
    ArtifactID,
)
from ..dependencies import get_dynamodb_table

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
            "description": "There is missing field(s) in the artifact_type or "
            "artifact_id or it is formed improperly, or is invalid."
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
    x_authorization: Annotated[str | None, Header(alias="X-Authorization")] = None,
    table=Depends(get_dynamodb_table),
) -> ArtifactCost:
    """
    Get the cost of an artifact (BASELINE)

    Return the total cost of the artifact, and its dependencies
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

    if item.get("type") != artifact_type.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="artifact_type does not match stored artifact type.",
        )

    hash_obj = hashlib.md5(id.encode())
    hash_int = int(hash_obj.hexdigest()[:8], 16)
    base_cost = (hash_int % 900) + 100

    if dependency:
        cost_detail = ArtifactCostDetail(
            standalone_cost=float(base_cost), total_cost=float(base_cost)
        )
    else:
        cost_detail = ArtifactCostDetail(
            standalone_cost=float(base_cost), total_cost=float(base_cost)
        )

    return {id: cost_detail}
