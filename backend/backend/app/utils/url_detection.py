"""URL detection and processing utilities for artifact ingestion."""

import re
from enum import Enum
from urllib.parse import urlparse


class URLType(str, Enum):
    """Type of URL source for artifact ingestion."""

    HUGGINGFACE = "huggingface"
    GITHUB = "github"
    DIRECT = "direct"


class URLInfo:
    """Information about a parsed URL."""

    def __init__(
        self, url: str, url_type: URLType, owner: str | None = None, repo: str | None = None
    ):
        """
        Initialize URL info.

        Args:
            url: The original URL
            url_type: The detected type of URL
            owner: Repository owner (for GitHub/HuggingFace)
            repo: Repository name (for GitHub/HuggingFace)
        """
        self.url = url
        self.url_type = url_type
        self.owner = owner
        self.repo = repo

    def __repr__(self) -> str:
        return f"URLInfo(url='{self.url}', type={self.url_type}, owner='{self.owner}', repo='{self.repo}')"


def detect_url_type(url: str) -> URLInfo:
    """
    Detect the type of URL and extract relevant information.

    Supported URL types:
    - HuggingFace: https://huggingface.co/{owner}/{repo}
    - GitHub: https://github.com/{owner}/{repo}
    - Direct: Any other URL (should point directly to a downloadable artifact)

    Args:
        url: The URL to analyze

    Returns:
        URLInfo object containing parsed information
    """
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    path = parsed.path.strip("/")

    # HuggingFace detection
    if "huggingface.co" in hostname:
        # Pattern: huggingface.co/{owner}/{repo}[/...]
        parts = path.split("/")
        if len(parts) >= 2:
            owner = parts[0]
            repo = parts[1]
            return URLInfo(url, URLType.HUGGINGFACE, owner=owner, repo=repo)
        return URLInfo(url, URLType.HUGGINGFACE)

    # GitHub detection
    if "github.com" in hostname:
        # GitHub repository URLs are exactly: github.com/{owner}/{repo}
        # Anything with more path segments or different patterns is not a repo
        parts = path.split("/")
        
        if len(parts) == 2:
            owner = parts[0]
            repo = parts[1]
            return URLInfo(url, URLType.GITHUB, owner=owner, repo=repo)
        
        # Not a repository URL pattern, treat as direct
        return URLInfo(url, URLType.DIRECT)

    # Everything else is treated as a direct URL
    return URLInfo(url, URLType.DIRECT)


def is_huggingface_url(url: str) -> bool:
    """Check if URL is a HuggingFace URL."""
    return detect_url_type(url).url_type == URLType.HUGGINGFACE


def is_github_url(url: str) -> bool:
    """Check if URL is a GitHub URL."""
    return detect_url_type(url).url_type == URLType.GITHUB


def is_direct_url(url: str) -> bool:
    """Check if URL is a direct download URL."""
    return detect_url_type(url).url_type == URLType.DIRECT


def extract_artifact_name(url: str) -> str:
    """
    Extract artifact name from URL.

    For HuggingFace URLs like https://huggingface.co/openai/whisper-tiny,
    extract 'whisper-tiny'.
    For GitHub URLs like https://github.com/openai/whisper, extract 'whisper'.
    For direct URLs, extract the filename without extension.

    Args:
        url: The URL to extract name from

    Returns:
        Extracted artifact name
    """
    url_info = detect_url_type(url)

    if url_info.url_type in (URLType.HUGGINGFACE, URLType.GITHUB):
        if url_info.repo:
            return url_info.repo

    # For direct URLs, try to extract filename
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if path:
        # Get the last part of the path
        filename = path.split("/")[-1]
        # Remove common archive extensions
        for ext in [".zip", ".tar.gz", ".tgz", ".tar", ".gz"]:
            if filename.endswith(ext):
                filename = filename[: -len(ext)]
        if filename:
            return filename

    return "unnamed-artifact"


def get_github_default_branch_zip_url(owner: str, repo: str, branch: str = "main") -> str:
    """
    Generate GitHub archive URL for downloading repository as zip.

    Args:
        owner: Repository owner
        repo: Repository name
        branch: Branch name (default: main)

    Returns:
        URL to download repository as zip file

    Example:
        >>> get_github_default_branch_zip_url("openai", "whisper")
        'https://github.com/openai/whisper/archive/refs/heads/main.zip'
    """
    return f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"


def get_huggingface_repo_url(owner: str, repo: str) -> str:
    """
    Generate HuggingFace repository URL.

    Args:
        owner: Repository owner
        repo: Repository name

    Returns:
        HuggingFace repository URL

    Example:
        >>> get_huggingface_repo_url("openai", "whisper-tiny")
        'https://huggingface.co/openai/whisper-tiny'
    """
    return f"https://huggingface.co/{owner}/{repo}"
