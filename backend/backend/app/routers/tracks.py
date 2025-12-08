"""Tracks information endpoint."""

from fastapi import APIRouter, HTTPException, status

from ..models import TracksResponse

router = APIRouter(
    prefix="/tracks",
    tags=["tracks"],
)

# Allowed enum values per OpenAPI spec.
ALLOWED_TRACKS = [
    "Performance track",
    "Access control track",
    "High assurance track",
    "Other Security track",
]

# Your team plans to implement only the Performance track.
PLANNED_TRACKS = ["Performance track"]


@router.get(
    "",
    response_model=TracksResponse,
    responses={
        200: {
            "description": "Return the list of tracks the student plans to implement",
        },
        500: {
            "description": "The system encountered an error while retrieving the student's track information.",
        },
    },
    summary="Get the list of tracks a student has planned to implement in their code",
)
async def get_tracks() -> TracksResponse:
    """
    Get the list of tracks a student has planned to implement in their code.

    Returns:
        TracksResponse: Object containing plannedTracks = [...]
    """
    # Defensive check so we never return an invalid value.
    for track in PLANNED_TRACKS:
        if track not in ALLOWED_TRACKS:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid track value: {track}",
            )

    return TracksResponse(plannedTracks=PLANNED_TRACKS)
