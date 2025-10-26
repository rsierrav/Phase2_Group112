"""Health check and monitoring endpoints."""

from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Query

from ..models import (
    HealthSummaryResponse,
    HealthComponentCollection,
)

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Service reachable."},
    },
)
async def registry_health_heartbeat() -> dict[str, str]:
    """
    Heartbeat check (BASELINE)

    Lightweight liveness probe. Returns HTTP 200 when the registry API is reachable.
    """
    # TODO: Implement actual health check logic
    # For now, return a simple status indicating the service is up
    return {"status": "ok"}


@router.get(
    "/components",
    response_model=HealthComponentCollection,
    responses={
        200: {"description": "Component-level health detail."},
    },
)
async def registry_health_components(
    window_minutes: Annotated[
        int,
        Query(
            description="Length of the trailing observation window, in minutes (5-1440). Defaults to 60.",
            ge=5,
            le=1440,
        ),
    ] = 60,
    include_timeline: Annotated[
        bool,
        Query(
            alias="includeTimeline",
            description="Set to true to include per-component activity timelines sampled across the window.",
        ),
    ] = False,
) -> HealthComponentCollection:
    """
    Get component health details (NON-BASELINE)

    Return per-component health diagnostics, including status, active issues, and log references.
    Use this endpoint to power deeper observability dashboards or for incident debugging.
    """
    # TODO: Implement component health check logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Endpoint not yet implemented"
    )
