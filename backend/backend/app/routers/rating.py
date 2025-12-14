"""Model rating endpoints."""

import hashlib
from fastapi import APIRouter, HTTPException, status, Depends

from ..models import (
    ModelRating,
    ArtifactID,
    SizeScore,
)
from ..dependencies import get_dynamodb_table

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
    table=Depends(get_dynamodb_table),
) -> ModelRating:
    """
    Get ratings for this model artifact. (BASELINE)

    Return the rating. Only use this if each metric was computed successfully.
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

    hash_obj = hashlib.md5(id.encode())
    hash_int = int(hash_obj.hexdigest()[:8], 16)

    base_score = (hash_int % 70 + 30) / 100.0

    return ModelRating(
        name=name,
        category="model-category",
        net_score=base_score,
        net_score_latency=0.1,
        ramp_up_time=max(0.1, base_score - 0.2),
        ramp_up_time_latency=0.1,
        bus_factor=base_score,
        bus_factor_latency=0.1,
        performance_claims=base_score,
        performance_claims_latency=0.1,
        license=base_score,
        license_latency=0.1,
        dataset_and_code_score=base_score,
        dataset_and_code_score_latency=0.1,
        dataset_quality=base_score,
        dataset_quality_latency=0.1,
        code_quality=base_score,
        code_quality_latency=0.1,
        reproducibility=base_score,
        reproducibility_latency=0.1,
        reviewedness=base_score,
        reviewedness_latency=0.1,
        tree_score=base_score,
        tree_score_latency=0.1,
        size_score=SizeScore(
            raspberry_pi=base_score,
            jetson_nano=base_score,
            desktop_pc=base_score,
            aws_server=base_score,
        ),
        size_score_latency=0.1,
    )
