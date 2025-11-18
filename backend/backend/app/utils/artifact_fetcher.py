"""Artifact fetching and packaging utilities."""

import io
import os
import shutil
import zipfile
import tempfile
from typing import BinaryIO
from pathlib import Path
import httpx
from huggingface_hub import snapshot_download

from .url_detection import (
    URLType,
    URLInfo,
    detect_url_type,
    get_github_default_branch_zip_url,
)


class ArtifactFetcher:
    """Service for fetching and packaging artifacts from various sources."""

    def __init__(self, timeout: int = 300):
        """
        Initialize artifact fetcher.

        Args:
            timeout: HTTP request timeout in seconds (default: 5 minutes)
        """
        self.timeout = timeout

    async def fetch_and_package(self, url: str) -> tuple[bytes, str]:
        """
        Fetch an artifact from a URL and package it as a zip if needed.

        Args:
            url: The source URL

        Returns:
            Tuple of (zip file content as bytes, artifact name)

        Raises:
            Exception: If fetching or packaging fails
        """
        url_info = detect_url_type(url)

        if url_info.url_type == URLType.GITHUB:
            return await self._fetch_github_repo(url_info)
        elif url_info.url_type == URLType.HUGGINGFACE:
            return await self._fetch_huggingface_repo(url_info)
        else:  # DIRECT
            return await self._fetch_direct_artifact(url_info)

    async def _fetch_github_repo(self, url_info: URLInfo) -> tuple[bytes, str]:
        """
        Fetch a GitHub repository as a zip archive.

        Args:
            url_info: Parsed URL information

        Returns:
            Tuple of (zip file content, artifact name)
        """
        if not url_info.owner or not url_info.repo:
            raise Exception("Invalid GitHub URL: missing owner or repo")

        # TODO(ryan): use github api for this
        # Try main branch first, then master
        zip_url: str | None = None
        for branch in ["main", "master"]:
            try:
                zip_url = get_github_default_branch_zip_url(url_info.owner, url_info.repo, branch)
                content = await self._download_file(zip_url)
                return content, url_info.repo
            except Exception as e:
                # Try next branch
                continue
        raise Exception(
            "Failed to download GitHub repository: could not find main or master branch."
        )

    async def _fetch_huggingface_repo(self, url_info: URLInfo) -> tuple[bytes, str]:
        """
        Fetch a HuggingFace repository as a zip archive.

        Uses the HuggingFace Hub API to download the repository snapshot
        and packages it as a zip file.

        Args:
            url_info: Parsed URL information

        Returns:
            Tuple of (zip file content, artifact name)

        Raises:
            Exception: If fetching fails
        """
        if not url_info.owner or not url_info.repo:
            raise Exception("Invalid HuggingFace URL: missing owner or repo")

        # Construct repo_id from owner and repo
        repo_id = f"{url_info.owner}/{url_info.repo}"

        # Create temporary directory for download
        temp_dir = tempfile.mkdtemp(prefix="hf_repo_")

        try:
            # Download repository snapshot to temporary directory
            # This downloads all files from the repository
            snapshot_path = snapshot_download(
                repo_id=repo_id,
                local_dir=temp_dir,
            )

            # Create zip archive from downloaded files
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                # Walk through all files in the downloaded directory
                for root, dirs, files in os.walk(snapshot_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Calculate relative path for archive
                        arcname = os.path.relpath(file_path, snapshot_path)
                        zip_file.write(file_path, arcname)

            return zip_buffer.getvalue(), url_info.repo

        except Exception as e:
            raise Exception(f"Failed to download HuggingFace repository {repo_id}: {str(e)}")

        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass  # Best effort cleanup

    async def _fetch_direct_artifact(self, url_info: URLInfo) -> tuple[bytes, str]:
        """
        Fetch a direct artifact URL.

        The URL should point directly to a downloadable file (zip, tar.gz, etc.).

        Args:
            url_info: Parsed URL information

        Returns:
            Tuple of (file content, artifact name)
        """
        content = await self._download_file(url_info.url)

        # Extract name from URL
        from .url_detection import extract_artifact_name

        name = extract_artifact_name(url_info.url)

        # Check if it's already a zip file
        if self._is_zip_file(content):
            return content, name

        # If not a zip, wrap it in one
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Determine filename from URL
            parsed_path = url_info.url.split("/")[-1]
            if not parsed_path:
                parsed_path = "artifact"
            zip_file.writestr(parsed_path, content)

        return zip_buffer.getvalue(), name

    async def _download_file(self, url: str) -> bytes:
        """
        Download a file from a URL.

        Args:
            url: The URL to download from

        Returns:
            File content as bytes

        Raises:
            Exception: If download fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
        except httpx.HTTPError as e:
            raise Exception(f"Failed to download file from {url}: {str(e)}")

    def _is_zip_file(self, content: bytes) -> bool:
        """
        Check if content is a valid zip file.

        Args:
            content: File content to check

        Returns:
            True if content is a zip file, False otherwise
        """
        try:
            with io.BytesIO(content) as buffer:
                with zipfile.ZipFile(buffer, "r") as _:
                    return True
        except Exception:
            return False


def get_artifact_fetcher() -> ArtifactFetcher:
    """Get an artifact fetcher instance."""
    return ArtifactFetcher()
