"""Service for handling artifact ingestion workflow."""

from typing import Optional
import logging

from ..models import Artifact, ArtifactData, ArtifactType
from ..db.dynamodb import get_db_service, DynamoDBService
from ..db.s3 import get_s3_service, S3Service
from ..utils.url_detection import detect_url_type, URLType
from ..utils.artifact_fetcher import get_artifact_fetcher, ArtifactFetcher

logger = logging.getLogger(__name__)


class ArtifactIngestionService:
    """Service orchestrating the complete artifact ingestion workflow."""

    def __init__(
        self,
        db_service: Optional[DynamoDBService] = None,
        s3_service: Optional[S3Service] = None,
        artifact_fetcher: Optional[ArtifactFetcher] = None,
    ):
        """
        Initialize the ingestion service.

        Args:
            db_service: DynamoDB service instance (creates one if not provided)
            s3_service: S3 service instance (creates one if not provided)
            artifact_fetcher: Artifact fetcher instance (creates one if not provided)
        """
        self.db_service = db_service or get_db_service()
        self.s3_service = s3_service or get_s3_service()
        self.artifact_fetcher = artifact_fetcher or get_artifact_fetcher()

    async def ingest_artifact(
        self, artifact_data: ArtifactData, artifact_type: ArtifactType
    ) -> Artifact:
        """
        Complete workflow for ingesting an artifact.

        Steps:
        1. Create artifact metadata in DynamoDB
        2. Detect URL type and fetch artifact
        3. Upload to S3
        4. Update DynamoDB with S3 information
        5. Return complete artifact with download URL

        Args:
            artifact_data: Artifact data including source URL
            artifact_type: Type of artifact (model/dataset/code)

        Returns:
            Complete artifact with metadata and download URL

        Raises:
            Exception: If any step fails
        """
        url = str(artifact_data.url)
        logger.info(f"Starting ingestion for URL: {url}")

        # Step 1: Detect URL type
        url_info = detect_url_type(url)
        logger.info(f"Detected URL type: {url_info.url_type}")

        # Step 2: Create artifact metadata in DynamoDB
        try:
            artifact = await self.db_service.create_artifact(artifact_data, artifact_type)
            logger.info(f"Created artifact with ID: {artifact.metadata.id}")
        except Exception as e:
            logger.error(f"Failed to create artifact in database: {e}")
            raise Exception(f"Failed to create artifact metadata: {str(e)}")

        # Step 3: Fetch and package the artifact
        try:
            zip_file_path, artifact_name = await self.artifact_fetcher.fetch_and_package(url)
            logger.info(
                f"Fetched and packaged artifact: {artifact_name} (saved to {zip_file_path})"
            )
        except Exception as e:
            logger.error(f"Failed to fetch artifact: {e}")
            # Could optionally delete the artifact metadata here
            raise Exception(f"Failed to fetch artifact from source: {str(e)}")

        # Step 4: Upload to S3
        try:
            s3_object_key = await self.s3_service.upload_artifact(
                file_content=zip_file_path,  # Pass file path for streaming upload
                artifact_id=artifact.metadata.id,
                artifact_type=artifact_type.value,
                name=artifact.metadata.name,
            )
            logger.info(f"Uploaded to S3: {s3_object_key}")
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            # Could optionally delete the artifact metadata here
            raise Exception(f"Failed to store artifact in S3: {str(e)}")
        finally:
            # Clean up the temporary file
            try:
                import os
                os.unlink(zip_file_path)
                logger.info(f"Cleaned up temporary file: {zip_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary file {zip_file_path}: {cleanup_error}")

        # Step 5: Generate download URL
        try:
            download_url = await self.s3_service.generate_download_url(s3_object_key)
            logger.info("Generated download URL")
        except Exception as e:
            logger.error(f"Failed to generate download URL: {e}")
            # Continue anyway, we can generate the URL later
            download_url = None

        # Step 6: Update DynamoDB with S3 information
        if download_url:
            try:
                await self.db_service.update_artifact_storage(
                    artifact_id=artifact.metadata.id,
                    s3_object_key=s3_object_key,
                    download_url=download_url,
                )
                logger.info("Updated artifact with storage information")

                # Update the artifact object with download URL
                artifact.data.download_url = download_url  # type: ignore
            except Exception as e:
                logger.error(f"Failed to update artifact storage info: {e}")
                # Non-critical, continue anyway

        return artifact

    async def get_artifact_with_fresh_url(self, artifact_id: str) -> Optional[Artifact]:
        """
        Get an artifact and regenerate its download URL if needed.

        Args:
            artifact_id: The unique artifact identifier

        Returns:
            Artifact with fresh download URL, or None if not found
        """
        # Get artifact from database
        artifact = await self.db_service.get_artifact(artifact_id)
        if not artifact:
            return None

        # Get S3 object key
        s3_object_key = await self.db_service.get_s3_object_key(artifact_id)
        if not s3_object_key:
            return artifact

        # Generate fresh download URL
        try:
            download_url = await self.s3_service.generate_download_url(s3_object_key)
            artifact.data.download_url = download_url  # type: ignore

            # Optionally update the database with new URL
            await self.db_service.update_artifact_storage(
                artifact_id=artifact_id,
                s3_object_key=s3_object_key,
                download_url=download_url,
            )
        except Exception as e:
            logger.warning(f"Failed to generate fresh download URL: {e}")

        return artifact


def get_ingestion_service() -> ArtifactIngestionService:
    """Get or create the artifact ingestion service."""
    return ArtifactIngestionService()
