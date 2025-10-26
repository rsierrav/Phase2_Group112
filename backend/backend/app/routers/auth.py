"""Authentication endpoints."""

from fastapi import APIRouter, HTTPException, status

from ..models import (
    AuthenticationRequest,
    AuthenticationToken,
)

router = APIRouter(
    prefix="/authenticate",
    tags=["auth"],
)


@router.put(
    "",
    response_model=str,
    responses={
        200: {"description": "Return an AuthenticationToken."},
        400: {
            "description": "There is missing field(s) in the AuthenticationRequest or it is formed improperly."
        },
        401: {"description": "The user or password is invalid."},
        501: {"description": "This system does not support authentication."},
    },
)
async def create_auth_token(
    auth_request: AuthenticationRequest,
) -> str:
    """
    Authenticate this user -- get an access token. (NON-BASELINE)

    If your system supports the authentication scheme described in the spec, then:
    1. The obtained token should be provided to the other endpoints via the "X-Authorization" header.
    2. The "Authorization" header is *required* in your system.

    Otherwise, this endpoint should return HTTP 501 "Not implemented", and the
    "X-Authorization" header should be unused for the other endpoints.
    """
    # TODO: Implement authentication logic
    # For now, return 501 Not Implemented
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This system does not support authentication.",
    )
