"""Dependencies for authentication and common functionality."""

from typing import Annotated
from fastapi import Header
import os
import boto3

from .models import AuthenticationToken


async def get_auth_token(
    x_authorization: Annotated[str, Header(alias="X-Authorization")],
) -> AuthenticationToken:
    """
    Validate and extract authentication token from X-Authorization header.
    """
    return x_authorization


async def get_optional_auth_token(
    x_authorization: Annotated[str | None, Header()] = None,
) -> AuthenticationToken | None:
    return x_authorization


# DynamoDB dependency for endpoints that need the artifacts table.
AWS_REGION = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"

_dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)


async def get_dynamodb_table():
    """
    Provide a DynamoDB table reference for dependencies.
    """
    table_name = os.environ.get("ARTIFACTS_TABLE_NAME", "artifacts")
    return _dynamodb.Table(table_name)  # type: ignore[reportAttributeAccessIssue]
