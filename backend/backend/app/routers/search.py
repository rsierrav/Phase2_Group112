"""Artifact search endpoints."""

import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..dependencies import get_dynamodb_table

router = APIRouter(prefix="/artifact", tags=["search"])


class ArtifactSearchHit(BaseModel):
    name: str
    id: str
    type: str


@router.post(
    "/byRegEx",
    response_model=list[ArtifactSearchHit],
    responses={
        200: {"description": "Return a list of artifacts."},
        400: {"description": "Invalid regex or malformed request."},
        404: {"description": "No artifact found under this regex."},
    },
)
async def artifact_by_regex_post(
    body: dict,
    table=Depends(get_dynamodb_table),
) -> list[ArtifactSearchHit]:

    if "regex" not in body or not isinstance(body["regex"], str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request body")

    pattern = body["regex"]

    try:
        rx = re.compile(pattern)
    except re.error as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid regex: {e}")

    hits: list[ArtifactSearchHit] = []
    scan_kwargs = {}
    while True:
        resp = table.scan(**scan_kwargs)
        items = resp.get("Items", [])

        for item in items:
            name = item.get("name")
            art_id = item.get("id")
            art_type = item.get("type")

            if isinstance(name, str) and rx.search(name):
                if art_id is not None and art_type is not None:
                    hits.append(ArtifactSearchHit(name=name, id=str(art_id), type=str(art_type)))

        last_key = resp.get("LastEvaluatedKey")
        if not last_key:
            break
        scan_kwargs["ExclusiveStartKey"] = last_key

    if not hits:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No artifact found under this regex."
        )

    return hits
