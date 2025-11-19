"""S3 service layer for artifact storage."""

import io
import zipfile
import tempfile
from typing import BinaryIO
from functools import lru_cache
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError

from ..config import get_settings


class S3Service:
    """Service for interacting with S3 for artifact storage."""

    def __init__(self):
        """Initialize S3 service."""
        settings = get_settings()
        self.bucket_name = settings.S3_BUCKET_NAME

        if settings.S3_ENDPOINT_URL:
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID or "test",
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or "test",
            )
        else:
            self.s3_client = boto3.client("s3", region_name=settings.AWS_REGION)

        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                # Bucket doesn't exist, create it
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                except ClientError as create_error:
                    # Ignore error if bucket was created by another process
                    if "BucketAlreadyOwnedByYou" not in str(create_error):
                        raise
            else:
                raise

    def generate_object_key(self, artifact_id: str, artifact_type: str, name: str) -> str:
        """
        Generate S3 object key for an artifact.

        Format: {artifact_type}/{artifact_id}/{name}.zip
        Example: model/1234567890/bert-base-uncased.zip

        Args:
            artifact_id: Unique identifier for the artifact
            artifact_type: Type of artifact (model/dataset/code)
            name: Name of the artifact

        Returns:
            S3 object key string
        """
        # Sanitize name to remove invalid characters
        safe_name = name.replace("/", "-").replace("\\", "-")
        return f"{artifact_type}/{artifact_id}/{safe_name}.zip"

    async def upload_artifact(
        self,
        file_content: bytes | BinaryIO | str,
        artifact_id: str,
        artifact_type: str,
        name: str,
        content_type: str = "application/zip",
    ) -> str:
        """
        Upload an artifact to S3.
        
        Supports streaming uploads for large files using file paths or file-like objects
        to avoid loading entire files into memory.

        Args:
            file_content: File content as bytes, file-like object, or path to file on disk
            artifact_id: Unique identifier for the artifact
            artifact_type: Type of artifact (model/dataset/code)
            name: Name of the artifact
            content_type: MIME type of the file

        Returns:
            S3 object key of the uploaded file

        Raises:
            ClientError: If upload fails
        """
        object_key = self.generate_object_key(artifact_id, artifact_type, name)

        try:
            if isinstance(file_content, bytes):
                # Small files - upload directly from memory
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_key,
                    Body=file_content,
                    ContentType=content_type,
                )
            elif isinstance(file_content, str):
                # File path - stream from disk
                with open(file_content, 'rb') as f:
                    self.s3_client.upload_fileobj(
                        f,
                        self.bucket_name,
                        object_key,
                        ExtraArgs={"ContentType": content_type},
                    )
            else:
                # File-like object - stream directly
                self.s3_client.upload_fileobj(
                    file_content,
                    self.bucket_name,
                    object_key,
                    ExtraArgs={"ContentType": content_type},
                )

            return object_key
        except ClientError as e:
            raise Exception(f"Failed to upload artifact to S3: {str(e)}")

    async def generate_download_url(self, object_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for downloading an artifact.

        Args:
            object_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL string

        Raises:
            ClientError: If URL generation fails
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_key},
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            raise Exception(f"Failed to generate download URL: {str(e)}")

    async def delete_artifact(self, object_key: str) -> None:
        """
        Delete an artifact from S3.

        Args:
            object_key: S3 object key

        Raises:
            ClientError: If deletion fails
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)
        except ClientError as e:
            raise Exception(f"Failed to delete artifact from S3: {str(e)}")

    async def artifact_exists(self, object_key: str) -> bool:
        """
        Check if an artifact exists in S3.

        Args:
            object_key: S3 object key

        Returns:
            True if artifact exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                return False
            raise


@lru_cache(maxsize=1)
def get_s3_service() -> S3Service:
    """Get or create the S3 service singleton."""
    return S3Service()
