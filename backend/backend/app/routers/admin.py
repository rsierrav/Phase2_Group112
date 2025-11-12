"""Registry reset endpoint."""

from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Header

router = APIRouter(
    prefix="/reset",
    tags=["admin"],
)


@router.delete(
    "",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Registry is reset."},
        401: {"description": "You do not have permission to reset the registry."},
    },
)
async def registry_reset() -> dict[str, str]:
    """
    Reset the registry. (BASELINE)

    Reset the registry to a system default state.
    """
    # TODO: Implement registry reset logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Endpoint not yet implemented"
    )
