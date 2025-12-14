"""Artifact creation (ingestion) endpoints."""

from typing import Annotated, Optional
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

_RESERVED_TAIL_SEGMENTS = {
    "",
    "tree",
    "blob",
    "resolve",
    "raw",
    "download",
    "files",
    "main",
    "master",
    "dev",
    "trunk",
}


def _name_from_url(url: str) -> str:
    """
    Extract a stable artifact name from common artifact URLs.

    Examples:
      HF: https://huggingface.co/openai/whisper-tiny/tree/main -> whisper-tiny
      HF: https://huggingface.co/google-bert/bert-base-uncased -> bert-base-uncased
      GH: https://github.com/openai/whisper -> whisper
      GH: https://github.com/openai/whisper/tree/main -> whisper
    """
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]

    if not parts:
        return "artifact"

    host = (parsed.netloc or "").lower()

    # Hugging Face: /{owner}/{repo}/...
    if "huggingface.co" in host:
        # need at least owner/repo
        if len(parts) >= 2:
            return parts[1]

    # GitHub: /{owner}/{repo}/...
    if "github.com" in host:
        if len(parts) >= 2:
            return parts[1]

    # Generic fallback:
    # Walk backward and pick the last segment that's not a reserved "tail" token
    for seg in reversed(parts):
        if seg not in _RESERVED_TAIL_SEGMENTS:
            return seg

    # If everything was reserved somehow, pick a safe default
    return "artifact"


@router.post(
    "/{artifact_type}",
    status_code=status.HTTP_201_CREATED,
    response_model=Artifact,
    responses={
        201: {
            "description": ("Success. Check the id in the returned metadata for the official ID.")
        },
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
        400: {
            "description": (
                "There is missing field(s) in the artifact_data or it is formed "
                "improperly (must include a single url)."
            )
        },
        403: {
            "description": "Authentication failed due to invalid or missing AuthenticationToken."
        },
        409: {"description": "Artifact exists already."},
        424: {"description": "Artifact is not registered due to the disqualified rating."},
    },
)
async def artifact_create(
    artifact_type: ArtifactType,
    artifact_data: ArtifactData,
    x_authorization: Annotated[Optional[str], Header(alias="X-Authorization")] = None,
    table=Depends(get_dynamodb_table),
) -> Artifact:
    """
    Register a new artifact. (BASELINE)

    Baseline does not require auth; X-Authorization is ignored if present.
    """

    parsed = urlparse(str(artifact_data.url))
    if not parsed.scheme or not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "There is missing field(s) in the artifact_data or it is formed "
                "improperly (must include a single url)."
            ),
        )

    name = _name_from_url(str(artifact_data.url))
    artifact_id: ArtifactID = uuid4().hex

    item = {
        "id": artifact_id,
        "name": name,
        "type": artifact_type.value,
        "url": str(artifact_data.url),
        "metadata": {
            "id": artifact_id,
            "name": name,
            "type": artifact_type.value,
        },
        "data": {
            "url": str(artifact_data.url),
            "download_url": str(artifact_data.download_url or artifact_data.url),
        },
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
