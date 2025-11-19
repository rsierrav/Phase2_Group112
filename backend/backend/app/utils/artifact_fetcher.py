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

    async def fetch_and_package(self, url: str) -> tuple[str, str]:
        """
        Fetch an artifact from a URL and package it as a zip if needed.
        
        Downloads are streamed to temporary files on disk to avoid memory issues
        with large artifacts. The caller is responsible for deleting the temporary
        file when done.

        Args:
            url: The source URL

        Returns:
            Tuple of (path to temporary zip file, artifact name)
            The temporary file should be deleted by the caller using os.unlink() or similar.

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

    async def _fetch_github_repo(self, url_info: URLInfo) -> tuple[str, str]:
        """
        Fetch a GitHub repository as a zip archive.

        Args:
            url_info: Parsed URL information

        Returns:
            Tuple of (path to temp zip file, artifact name)
        """
        if not url_info.owner or not url_info.repo:
            raise Exception("Invalid GitHub URL: missing owner or repo")

        # TODO(ryan): use github api for this
        # Try main branch first, then master
        zip_url: str | None = None
        for branch in ["main", "master"]:
            try:
                zip_url = get_github_default_branch_zip_url(url_info.owner, url_info.repo, branch)
                file_path = await self._download_file_to_disk(zip_url)
                return file_path, url_info.repo
            except Exception as e:
                # Try next branch
                continue
        raise Exception(
            "Failed to download GitHub repository: could not find main or master branch."
        )

    async def _fetch_huggingface_repo(self, url_info: URLInfo) -> tuple[str, str]:
        """
        Fetch a HuggingFace repository as a zip archive.

        Uses the HuggingFace Hub API to download the repository snapshot
        and packages it as a zip file on disk.

        Args:
            url_info: Parsed URL information

        Returns:
            Tuple of (path to temp zip file, artifact name)

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

            # Create zip archive from downloaded files on disk
            # Use NamedTemporaryFile to create a temp file that persists after closing
            temp_zip = tempfile.NamedTemporaryFile(mode='wb', suffix='.zip', delete=False)
            temp_zip_path = temp_zip.name
            temp_zip.close()
            
            with zipfile.ZipFile(temp_zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                # Walk through all files in the downloaded directory
                for root, dirs, files in os.walk(snapshot_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Calculate relative path for archive
                        arcname = os.path.relpath(file_path, snapshot_path)
                        zip_file.write(file_path, arcname)

            return temp_zip_path, url_info.repo

        except Exception as e:
            raise Exception(f"Failed to download HuggingFace repository {repo_id}: {str(e)}")

        finally:
            # Clean up temporary directory (but not the zip file - caller's responsibility)
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass  # Best effort cleanup

    async def _fetch_direct_artifact(self, url_info: URLInfo) -> tuple[str, str]:
        """
        Fetch a direct artifact URL.

        The URL should point directly to a downloadable file (zip, tar.gz, etc.).

        Args:
            url_info: Parsed URL information

        Returns:
            Tuple of (path to temp file, artifact name)
        """
        file_path = await self._download_file_to_disk(url_info.url)

        # Extract name from URL
        from .url_detection import extract_artifact_name

        name = extract_artifact_name(url_info.url)

        # Check if it's already a zip file
        if self._is_zip_file_on_disk(file_path):
            return file_path, name

        # If not a zip, wrap it in one
        temp_zip = tempfile.NamedTemporaryFile(mode='wb', suffix='.zip', delete=False)
        temp_zip_path = temp_zip.name
        temp_zip.close()
        
        try:
            with zipfile.ZipFile(temp_zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                # Determine filename from URL
                parsed_path = url_info.url.split("/")[-1]
                if not parsed_path:
                    parsed_path = "artifact"
                zip_file.write(file_path, parsed_path)
            
            # Clean up the original downloaded file
            os.unlink(file_path)
            
            return temp_zip_path, name
        except Exception as e:
            # Clean up both files on error
            try:
                os.unlink(file_path)
            except:
                pass
            try:
                os.unlink(temp_zip_path)
            except:
                pass
            raise

    async def _download_file_to_disk(self, url: str) -> str:
        """
        Download a file from a URL and stream it to disk.
        
        Uses streaming to avoid loading large files into memory.

        Args:
            url: The URL to download from

        Returns:
            Path to the downloaded temporary file

        Raises:
            Exception: If download fails
        """
        try:
            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='wb', delete=False)
            temp_path = temp_file.name
            
            try:
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                    async with client.stream('GET', url) as response:
                        response.raise_for_status()
                        
                        # Stream the content to disk in chunks
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            temp_file.write(chunk)
                
                temp_file.close()
                return temp_path
                
            except Exception as e:
                temp_file.close()
                # Clean up the temp file on error
                try:
                    os.unlink(temp_path)
                except:
                    pass
                raise
                
        except httpx.HTTPError as e:
            raise Exception(f"Failed to download file from {url}: {str(e)}")

    def _is_zip_file_on_disk(self, file_path: str) -> bool:
        """
        Check if a file on disk is a valid zip file.

        Args:
            file_path: Path to file to check

        Returns:
            True if file is a zip file, False otherwise
        """
        try:
            with zipfile.ZipFile(file_path, "r") as _:
                return True
        except Exception:
            return False


def get_artifact_fetcher() -> ArtifactFetcher:
    """Get an artifact fetcher instance."""
    return ArtifactFetcher()
