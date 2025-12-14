"""Model rating endpoints."""

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

    return ModelRating(
        name=name,
        category="dummy-category",
        net_score=0.5,
        net_score_latency=0.1,
        ramp_up_time=0.5,
        ramp_up_time_latency=0.1,
        bus_factor=0.5,
        bus_factor_latency=0.1,
        performance_claims=0.5,
        performance_claims_latency=0.1,
        license=0.5,
        license_latency=0.1,
        dataset_and_code_score=0.5,
        dataset_and_code_score_latency=0.1,
        dataset_quality=0.5,
        dataset_quality_latency=0.1,
        code_quality=0.5,
        code_quality_latency=0.1,
        reproducibility=0.5,
        reproducibility_latency=0.1,
        reviewedness=0.5,
        reviewedness_latency=0.1,
        tree_score=0.5,
        tree_score_latency=0.1,
        size_score=SizeScore(raspberry_pi=0.5, jetson_nano=0.5, desktop_pc=0.5, aws_server=0.5),
        size_score_latency=0.1,
    )
