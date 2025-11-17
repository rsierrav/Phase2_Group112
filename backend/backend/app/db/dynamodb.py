"""DynamoDB service layer for artifact metadata storage."""

from typing import Any
from datetime import datetime, timezone
import secrets
from functools import lru_cache
from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute

from ..models import (
    Artifact,
    ArtifactData,
    ArtifactMetadata,
    ArtifactType,
)
from ..config import get_settings


# Global Secondary Indexes
class NameIndex(GlobalSecondaryIndex):
    """GSI for querying by artifact name."""

    class Meta:
        index_name = "NameIndex"
        projection = AllProjection()

    name = UnicodeAttribute(hash_key=True)
    artifact_id = UnicodeAttribute(range_key=True)


class TypeIndex(GlobalSecondaryIndex):
    """GSI for querying by artifact type."""

    class Meta:
        index_name = "TypeIndex"
        projection = AllProjection()

    artifact_type = UnicodeAttribute(hash_key=True)
    artifact_id = UnicodeAttribute(range_key=True)


class ArtifactModel(Model):
    """DynamoDB model for artifacts"""

    class Meta:
        settings = get_settings()
        table_name = settings.ARTIFACTS_TABLE_NAME
        region = settings.AWS_REGION
        if settings.DYNAMODB_ENDPOINT_URL:
            host = settings.DYNAMODB_ENDPOINT_URL

    # Primary key
    PK = UnicodeAttribute(hash_key=True)
    SK = UnicodeAttribute(range_key=True)

    # Attributes
    artifact_id = UnicodeAttribute()
    name = UnicodeAttribute()
    artifact_type = UnicodeAttribute()
    url = UnicodeAttribute()
    download_url = UnicodeAttribute(null=True)
    created_at = UTCDateTimeAttribute()
    updated_at = UTCDateTimeAttribute()

    # Global Secondary Indexes
    name_index = NameIndex()
    type_index = TypeIndex()


class DynamoDBService:
    """Service for interacting with DynamoDB tables using PynamoDB."""

    def __init__(self):
        """Initialize DynamoDB service."""
        # PynamoDB handles connection automatically
        settings = get_settings()
        if settings.CREATE_TABLE:
            if not ArtifactModel.exists():
                ArtifactModel.create_table(billing_mode="PAY_PER_REQUEST", wait=True)

    def _generate_artifact_id(self) -> str:
        """Generate a unique artifact ID."""
        # TODO: Make this more robust. Can we use UUIDs?
        return str(secrets.randbelow(10**10)).zfill(10)

    def _model_to_artifact(self, model: ArtifactModel) -> Artifact:
        """Convert PynamoDB model to Artifact."""
        from pydantic import HttpUrl

        return Artifact(
            metadata=ArtifactMetadata(
                name=model.name,
                id=model.artifact_id,
                type=ArtifactType(model.artifact_type),
            ),
            data=ArtifactData(
                url=HttpUrl(str(model.url)),
                download_url=HttpUrl(str(model.download_url)) if model.download_url else None,
            ),
        )

    def _model_to_metadata(self, model: ArtifactModel) -> ArtifactMetadata:
        """Convert PynamoDB model to ArtifactMetadata."""
        return ArtifactMetadata(
            name=model.name,
            id=model.artifact_id,
            type=ArtifactType(model.artifact_type),
        )

    async def create_artifact(
        self, artifact_data: ArtifactData, artifact_type: ArtifactType
    ) -> Artifact:
        """
        Create a new artifact in DynamoDB.

        Args:
            artifact_data: The artifact data including URL
            artifact_type: The type of artifact (model/dataset/code)

        Returns:
            The created artifact with metadata

        Raises:
            Exception: If artifact creation fails
        """
        # Generate unique artifact ID
        artifact_id = self._generate_artifact_id()

        # Extract name from URL
        name = self._extract_name_from_url(str(artifact_data.url))

        # Create artifact object
        artifact = Artifact(
            metadata=ArtifactMetadata(
                name=name,
                id=artifact_id,
                type=artifact_type,
            ),
            data=artifact_data,
        )

        # Create PynamoDB model instance
        now = datetime.now(timezone.utc)
        model = ArtifactModel(
            PK=artifact_id,
            SK="METADATA",
            artifact_id=artifact_id,
            name=name,
            artifact_type=artifact_type.value,
            url=str(artifact_data.url),
            download_url=str(artifact_data.download_url) if artifact_data.download_url else None,
            created_at=now,
            updated_at=now,
        )

        try:
            # Save with condition that PK doesn't exist
            _ = model.save(condition=(ArtifactModel.PK.does_not_exist()))
        except Exception as e:
            if "ConditionalCheckFailedException" in str(e):
                raise Exception("Artifact ID collision occurred")
            raise

        return artifact

    def _extract_name_from_url(self, url: str) -> str:
        """
        Extract artifact name from URL.

        For HuggingFace URLs like https://huggingface.co/google-bert/bert-base-uncased,
        extract 'bert-base-uncased'.
        For GitHub URLs like https://github.com/openai/whisper, extract 'whisper'.
        """
        url = url.rstrip("/")
        parts = url.split("/")
        if len(parts) >= 2:
            return parts[-1]
        return "unnamed-artifact"

    async def get_artifact(self, artifact_id: str) -> Artifact | None:
        """
        Get an artifact by its ID.

        Args:
            artifact_id: The unique artifact identifier

        Returns:
            The artifact if found, None otherwise
        """
        try:
            model = ArtifactModel.get(artifact_id, "METADATA")
            return self._model_to_artifact(model)
        except Exception:  # PynamoDB's DoesNotExist exception
            return None

    async def list_artifacts_by_type(
        self,
        artifact_type: ArtifactType,
        limit: int = 10,
        last_evaluated_key: dict[str, Any] | None = None,
    ) -> tuple[list[ArtifactMetadata], dict[str, Any] | None]:
        """
        List artifacts by type using GSI.

        Args:
            artifact_type: The type to filter by
            limit: Maximum number of items to return
            last_evaluated_key: Pagination token from previous query

        Returns:
            Tuple of (list of artifact metadata, next pagination token)
        """
        try:
            results = ArtifactModel.type_index.query(
                artifact_type.value,
                limit=limit,
                last_evaluated_key=last_evaluated_key,
            )

            artifacts = []
            next_key = None
            for model in results:
                artifacts.append(self._model_to_metadata(model))
                if len(artifacts) >= limit:
                    next_key = results.last_evaluated_key
                    break

            return artifacts, next_key
        except Exception:
            return [], None

    async def scan_all_artifacts(
        self,
        limit: int = 10,
        last_evaluated_key: dict[str, Any] | None = None,
    ) -> tuple[list[ArtifactMetadata], dict[str, Any] | None]:
        """
        Scan all artifacts (for enumerate with name="*").

        Args:
            limit: Maximum number of items to return
            last_evaluated_key: Pagination token from previous scan

        Returns:
            Tuple of (list of artifact metadata, next pagination token)
        """
        try:
            results = ArtifactModel.scan(
                filter_condition=(ArtifactModel.SK == "METADATA"),
                limit=limit,
                last_evaluated_key=last_evaluated_key,
            )

            artifacts = []
            next_key = None
            for model in results:
                artifacts.append(self._model_to_metadata(model))
                if len(artifacts) >= limit:
                    next_key = results.last_evaluated_key
                    break

            return artifacts, next_key
        except Exception:
            return [], None

    async def query_artifacts_by_name(
        self,
        name: str,
        artifact_types: list[ArtifactType] | None = None,
        limit: int = 10,
        last_evaluated_key: dict[str, Any] | None = None,
    ) -> tuple[list[ArtifactMetadata], dict[str, Any] | None]:
        """
        Query artifacts by name using GSI.

        Args:
            name: The artifact name to search for
            artifact_types: Optional list of types to filter by
            limit: Maximum number of items to return
            last_evaluated_key: Pagination token from previous query

        Returns:
            Tuple of (list of artifact metadata, next pagination token)
        """
        try:
            filter_condition = None
            if artifact_types:
                type_values = [t.value for t in artifact_types]
                filter_condition = ArtifactModel.artifact_type.is_in(*type_values)

            results = ArtifactModel.name_index.query(
                name,
                filter_condition=filter_condition,
                limit=limit,
                last_evaluated_key=last_evaluated_key,
            )

            artifacts = []
            next_key = None
            for model in results:
                artifacts.append(self._model_to_metadata(model))
                if len(artifacts) >= limit:
                    next_key = results.last_evaluated_key
                    break

            return artifacts, next_key
        except Exception:
            return [], None


@lru_cache(maxsize=1)
def get_db_service() -> DynamoDBService:
    """Get or create the DynamoDB service singleton."""
    return DynamoDBService()
