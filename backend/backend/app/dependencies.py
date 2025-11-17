"""Dependencies for authentication and common functionality."""

from typing import Annotated
from fastapi import Header, HTTPException, status

from .models import AuthenticationToken


async def get_auth_token(
    x_authorization: Annotated[str, Header(alias="X-Authorization")],
) -> AuthenticationToken:
    """
    Validate and extract authentication token from X-Authorization header.

    Raises:
        HTTPException: 403 if token is missing or invalid
    """
    # TODO: Implement actual token validation logic
    # For now, just return the token
    return x_authorization


async def get_optional_auth_token(
    x_authorization: Annotated[str | None, Header()] = None,
) -> AuthenticationToken | None:
    """
    Extract authentication token from X-Authorization header without validation.
    Used for endpoints that may have optional authentication.
    """
    return x_authorization
