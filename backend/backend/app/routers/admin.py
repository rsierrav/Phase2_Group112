"""Registry reset endpoint."""

from fastapi import APIRouter, HTTPException, status, Depends

from ..dependencies import get_dynamodb_table

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
async def registry_reset(
    table=Depends(get_dynamodb_table),
) -> dict[str, str]:
    """
    Reset the registry. (BASELINE)

    Reset the registry to a system default state.
    """
    try:
        scan_kwargs: dict = {}
        while True:
            resp = table.scan(**scan_kwargs)
            items = resp.get("Items", [])

            if items:
                with table.batch_writer() as batch:
                    for item in items:
                        batch.delete_item(Key={"id": item["id"]})

            last_key = resp.get("LastEvaluatedKey")
            if not last_key:
                break
            scan_kwargs["ExclusiveStartKey"] = last_key

    except Exception as exc:  # noqa: BLE001
        print(f"Error resetting registry: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset the registry.",
        )

    return {"status": "reset"}
