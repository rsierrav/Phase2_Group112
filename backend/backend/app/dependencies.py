"""Dependencies for authentication and common functionality."""

from typing import Annotated
from fastapi import Header
import os
import boto3
from boto3.resources.base import ServiceResource

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


def _create_dynamodb_resource() -> ServiceResource:
    """Create a DynamoDB resource with a default region for local/dev."""
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
    return boto3.resource("dynamodb", region_name=region)


_dynamodb = _create_dynamodb_resource()


async def get_dynamodb_table():
    """
    Provide a DynamoDB table reference for dependencies.
    """
    table_name = os.environ.get("ARTIFACTS_TABLE_NAME", "artifacts")
    return _dynamodb.Table(table_name)  # type: ignore[reportAttributeAccessIssue]
