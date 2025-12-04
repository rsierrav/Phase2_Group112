from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from boto3.dynamodb.conditions import Attr
from mypy_boto3_dynamodb.service_resource import Table  # type: ignore[import]
from ..models import EnumerateOffset


def query_artifacts_by_name(
    table: Table,
    name: str,
    artifact_types: Optional[List[str]] = None,
    limit: int = 100,
    last_evaluated_key: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Query artifacts by name (supports wildcard '*' via contains) and optional types.
    Uses a DynamoDB Scan with FilterExpression and Limit + ExclusiveStartKey.
    """
    scan_kwargs: Dict[str, Any] = {
        "Limit": limit,
    }

    filter_expr = None

    if name != "*":
        name_expr = Attr("name").contains(name)
        filter_expr = name_expr if filter_expr is None else filter_expr & name_expr

    if artifact_types:
        type_expr = Attr("type").is_in(artifact_types)
        filter_expr = type_expr if filter_expr is None else filter_expr & type_expr

    if filter_expr is not None:
        scan_kwargs["FilterExpression"] = filter_expr

    if last_evaluated_key:
        scan_kwargs["ExclusiveStartKey"] = last_evaluated_key

    response = table.scan(**scan_kwargs)

    items = response.get("Items", []) or []
    next_key = response.get("LastEvaluatedKey")
    return items, next_key


def parse_pagination_token(offset: Optional[EnumerateOffset]) -> Optional[Dict[str, Any]]:
    """
    Convert an offset (opaque pagination token) into a DynamoDB LastEvaluatedKey dict.
    For now, if offset is None, we simply start from the beginning.
    """
    if offset is None:
        return None
    # If EnumerateOffset already wraps the key dict, just return it.
    # Adjust this if your EnumerateOffset type is different.
    return offset.key if hasattr(offset, "key") else None  # type: ignore[attr-defined]


def encode_pagination_token(last_evaluated_key: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Convert a LastEvaluatedKey dict into an opaque string token.
    For now, we use a simple JSON representation.
    """
    if last_evaluated_key is None:
        return None

    import json

    return json.dumps(last_evaluated_key)


def format_artifact_metadata(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map raw DynamoDB item into the shape expected by ArtifactMetadata.
    Adjust field names here as needed to match your table schema.
    """
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "type": item.get("type"),
        "owner": item.get("owner"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        # include any other fields your ArtifactMetadata model expects
    }
