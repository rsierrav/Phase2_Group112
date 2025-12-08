"""Artifact creation (ingestion) endpoints."""

from typing import Annotated
from uuid import uuid4
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, status, Header, Depends

from ..models import (
    Artifact,
    ArtifactData,
    ArtifactMetadata,
    ArtifactType,
    ArtifactID,
)
from ..dependencies import get_dynamodb_table

router = APIRouter(
    prefix="/artifact",
    tags=["artifact-ingest"],
)


@router.post(
    "/{artifact_type}",
    status_code=status.HTTP_201_CREATED,
    response_model=Artifact,
    responses={
        201: {"description": ("Success. Check the id in the returned metadata for the official ID.")},
        202: {
            "description": (
                "Artifact ingest accepted but the rating pipeline deferred the "
                "evaluation. Use this when the package is stored but rating is "
                "performed asynchronously and the artifact is dropped silently "
                "if the rating later fails. Subsequent requests to `/rate` or any "
                "other endpoint with this artifact id should return 404 until a "
                "rating result exists."
            )
        },
        400: {"description": ("There is missing field(s) in the artifact_data or it is formed " "improperly (must include a single url).")},
        403: {"description": "Authentication failed due to invalid or missing AuthenticationToken."},
        409: {"description": "Artifact exists already."},
        424: {"description": "Artifact is not registered due to the disqualified rating."},
    },
)
async def artifact_create(
    artifact_type: ArtifactType,
    artifact_data: ArtifactData,
    x_authorization: Annotated[str, Header(alias="X-Authorization")],
    table=Depends(get_dynamodb_table),
) -> Artifact:
    """
    Register a new artifact. (BASELINE)

    Register a new artifact by providing a downloadable source url.
    Artifacts may share a name with existing entries; refer to the description
    above to see how an id is formed for an artifact.
    """
    if not x_authorization:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication failed due to invalid or missing AuthenticationToken.",
        )

    parsed = urlparse(str(artifact_data.url))
    if not parsed.scheme or not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("There is missing field(s) in the artifact_data or it is formed " "improperly (must include a single url)."),
        )

    name = parsed.path.rstrip("/").split("/")[-1] or "artifact"

    artifact_id: ArtifactID = uuid4().hex

    item = {
        "id": artifact_id,
        "name": name,
        "type": artifact_type.value,
        "url": str(artifact_data.url),
    }

    try:
        table.put_item(Item=item)
    except Exception as exc:  # noqa: BLE001
        print(f"Error writing artifact to DynamoDB: {exc}")
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail="Artifact is not registered due to an internal storage error.",
        )

    metadata = ArtifactMetadata(
        id=artifact_id,
        name=name,
        type=artifact_type,
    )
    data = ArtifactData(
        url=artifact_data.url,
        download_url=artifact_data.download_url or artifact_data.url,
    )

    return Artifact(metadata=metadata, data=data)
