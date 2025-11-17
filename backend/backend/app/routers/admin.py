"""Registry reset endpoint."""

from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends

from app.db.dynamodb import DynamoDBService, get_db_service

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
async def registry_reset(db: DynamoDBService = Depends(get_db_service)) -> None:
    """
    Reset the registry. (BASELINE)

    Reset the registry to a system default state.
    """
    db.reset_table()
