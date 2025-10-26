"""Tracks information endpoint."""

from fastapi import APIRouter, HTTPException, status

from ..models import TracksResponse

router = APIRouter(
    prefix="/tracks",
    tags=["tracks"],
)


@router.get(
    "",
    response_model=TracksResponse,
    responses={
        200: {"description": "Return the list of tracks the student plans to implement"},
        500: {
            "description": "The system encountered an error while retrieving the student's track information."
        },
    },
)
async def get_tracks() -> TracksResponse:
    """
    Get the list of tracks a student has planned to implement in their code.

    Return the list of tracks the student plans to implement.
    """
    # TODO: Implement tracks retrieval logic
    # For now, return an empty list or raise not implemented
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Endpoint not yet implemented"
    )
