"""Artifact audit trail endpoints."""

from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Header

from ..models import (
    ArtifactAuditEntry,
    ArtifactType,
    ArtifactID,
)

router = APIRouter(
    prefix="/artifact",
    tags=["audit"],
)


@router.get(
    "/{artifact_type}/{id}/audit",
    response_model=list[ArtifactAuditEntry],
    responses={
        200: {"description": "Return the audit trail for this artifact."},
        400: {
            "description": "There is missing field(s) in the artifact_type or artifact_id or it is formed improperly, or is invalid."
        },
        404: {"description": "Artifact does not exist."},
    },
)
async def artifact_audit_get(
    artifact_type: ArtifactType,
    id: ArtifactID,
) -> list[ArtifactAuditEntry]:
    """
    Retrieve audit entries for this artifact. (NON-BASELINE)

    Return the audit trail for this artifact.
    """
    # TODO: Implement audit trail retrieval logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Endpoint not yet implemented"
    )
