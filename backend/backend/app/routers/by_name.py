"""Artifact by name endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from botocore.exceptions import ClientError
from pydantic import BaseModel

from ..dependencies import get_dynamodb_table

router = APIRouter(prefix="/artifact", tags=["search"])


class ArtifactMetadata(BaseModel):
    name: str
    id: str
    type: str


@router.get(
    "/byName/{name}",
    response_model=list[ArtifactMetadata],
    responses={
        200: {"description": "Return artifact metadata entries that match the provided name."},
        400: {
            "description": "There is missing field(s) in the artifact_name or it is formed improperly, or is invalid."
        },
        403: {
            "description": "Authentication failed due to invalid or missing AuthenticationToken."
        },
        404: {"description": "No such artifact."},
    },
)
async def artifact_by_name_get(
    name: str,
    x_authorization: Optional[str] = Header(default=None, alias="X-Authorization"),
    table=Depends(get_dynamodb_table),
) -> list[ArtifactMetadata]:
    """
    List artifact metadata for this name. (NON-BASELINE)
    Return metadata for each artifact matching this name.
    """

    if not name or name.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is missing field(s) in the artifact_name or it is formed improperly, or is invalid.",
        )

    results = []
    scan_kwargs = {}

    try:
        while True:
            resp = table.scan(**scan_kwargs)
            items = resp.get("Items", [])

            for item in items:
                md = item.get("metadata") or {}

                artifact_name = md.get("name") or item.get("name")
                art_id = md.get("id") or item.get("id")
                art_type = md.get("type") or item.get("type")

                if not isinstance(artifact_name, str) or art_id is None or art_type is None:
                    continue

                if artifact_name == name:
                    results.append(
                        ArtifactMetadata(name=artifact_name, id=str(art_id), type=str(art_type))
                    )

            last_key = resp.get("LastEvaluatedKey")
            if not last_key:
                break
            scan_kwargs["ExclusiveStartKey"] = last_key

    except ClientError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The system encountered an error while searching artifacts.",
        )

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such artifact.",
        )

    return sorted(results, key=lambda x: x.id)
