"""Artifact search endpoints."""

from __future__ import annotations

import re
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from ..dependencies import get_dynamodb_table

router = APIRouter(prefix="/artifact", tags=["search"])


class ArtifactMetadata(BaseModel):
    name: str
    id: str
    type: str


_README_CACHE: dict[str, str] = {}

_MAX_NETWORK_README_FETCHES = 10


def _fetch_text(url: str, timeout: float = 0.75, max_bytes: int = 250_000) -> str:
    """Best-effort small GET. Returns '' on failure."""
    try:
        req = Request(url, headers={"User-Agent": "ece461-registry"})
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read(max_bytes)
        return data.decode("utf-8", errors="ignore")
    except (URLError, HTTPError, ValueError):
        return ""


def _github_owner_repo(url: str) -> Optional[tuple[str, str]]:
    if not isinstance(url, str) or "github.com/" not in url:
        return None
    try:
        path = url.split("github.com/", 1)[1].strip("/")
        parts = path.split("/")
        if len(parts) < 2:
            return None
        repo = parts[1]
        if repo.endswith(".git"):
            repo = repo[:-4]
        return parts[0], repo
    except Exception:
        return None


def _hf_owner_repo(url: str) -> Optional[tuple[str, str]]:
    if not isinstance(url, str) or "huggingface.co/" not in url:
        return None
    try:
        path = url.split("huggingface.co/", 1)[1].strip("/")
        parts = path.split("/")
        if len(parts) < 2:
            return None
        return parts[0], parts[1]
    except Exception:
        return None


def _extract_readme_text(item: dict) -> str:
    """
    Best-effort: pull README-like text from common DB fields.
    Autograders often store this locally to avoid network calls.
    """
    md = item.get("metadata") or {}
    data = item.get("data") or {}

    candidates = [
        item.get("readme"),
        item.get("README"),
        md.get("readme"),
        md.get("README"),
        data.get("readme"),
        data.get("README"),
        item.get("readme_text"),
        md.get("readme_text"),
        data.get("readme_text"),
    ]
    for c in candidates:
        if isinstance(c, str) and c.strip():
            return c
    return ""


def _readme_for_url(url: str) -> str:
    """
    Fast README fetch:
    - GitHub: raw.githubusercontent README
    - Hugging Face: /raw/main/README.md
    No HTML fallbacks.
    Cached.
    """
    if not url:
        return ""

    if url in _README_CACHE:
        return _README_CACHE[url]

    text = ""

    gh = _github_owner_repo(url)
    if gh:
        owner, repo = gh
        candidates = [
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md",
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.txt",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.txt",
        ]
        for c in candidates:
            text = _fetch_text(c)
            if text:
                break

    if not text:
        hf = _hf_owner_repo(url)
        if hf:
            owner, repo = hf
            base = f"https://huggingface.co/{owner}/{repo}"
            candidates = [
                f"{base}/raw/main/README.md",
                f"{base}/raw/master/README.md",
            ]
            for c in candidates:
                text = _fetch_text(c)
                if text:
                    break

    _README_CACHE[url] = text or ""
    return _README_CACHE[url]


def _compile_regex(pattern: str) -> tuple[re.Pattern, str]:
    """
    Compile a regex string.
    Supports:
      - Python regex: '^foo$'
      - JS-style: '/^foo$/i' or '/^foo$/' (flags optional; supported: i, m, s)
    Also strips redundant surrounding quotes: '"^foo$"' or "'^foo$'".
    """
    flags = 0
    pat = pattern.strip()

    # Strip surrounding quotes repeatedly
    while len(pat) >= 2 and ((pat[0] == pat[-1] == '"') or (pat[0] == pat[-1] == "'")):
        pat = pat[1:-1].strip()

    # JS-style /pattern/flags (flags optional)
    if len(pat) >= 2 and pat[0] == "/":
        last = pat.rfind("/")
        if last > 0:
            maybe_pat = pat[1:last]
            maybe_flags = pat[last + 1 :]  # noqa: E203

            if maybe_flags == "" or maybe_flags.isalpha():
                pat = maybe_pat
                if "i" in maybe_flags:
                    flags |= re.IGNORECASE
                if "m" in maybe_flags:
                    flags |= re.MULTILINE
                if "s" in maybe_flags:
                    flags |= re.DOTALL

    try:
        return re.compile(pat, flags), pat
    except re.error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is missing field(s) in the artifact_regex or it is formed improperly, or is invalid",
        )


def _name_matches(rx: re.Pattern, normalized_pattern: str, name: str) -> bool:
    # If anchored, require full match for names
    if normalized_pattern.startswith("^") and normalized_pattern.endswith("$"):
        return rx.fullmatch(name) is not None
    return rx.search(name) is not None


@router.post(
    "/byRegEx",
    response_model=list[ArtifactMetadata],
    responses={
        200: {"description": "Return a list of artifacts."},
        400: {
            "description": "There is missing field(s) in the artifact_regex or it is formed improperly, or is invalid"
        },
        403: {
            "description": "Authentication failed due to invalid or missing AuthenticationToken."
        },
        404: {"description": "No artifact found under this regex."},
    },
)
async def artifact_by_regex_post(
    body: dict,
    x_authorization: Optional[str] = Header(default=None, alias="X-Authorization"),
    table=Depends(get_dynamodb_table),
) -> list[ArtifactMetadata]:
    if "regex" not in body or not isinstance(body["regex"], str) or not body["regex"].strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is missing field(s) in the artifact_regex or it is formed improperly, or is invalid",
        )

    rx, normalized = _compile_regex(body["regex"])

    hits_by_id: dict[str, ArtifactMetadata] = {}

    scan_kwargs: dict = {}

    network_fetches = 0

    while True:
        try:
            resp = table.scan(**scan_kwargs)
        except ClientError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="The system encountered an error while searching artifacts.",
            )

        items = resp.get("Items", [])

        for item in items:
            md = item.get("metadata") or {}
            data = item.get("data") or {}

            name = md.get("name") or item.get("name")
            art_id = md.get("id") or item.get("id")
            art_type = md.get("type") or item.get("type")
            url = data.get("url") or item.get("url") or ""

            if not isinstance(name, str) or art_id is None or art_type is None:
                continue

            art_id_str = str(art_id)
            art_type_str = str(art_type)

            if _name_matches(rx, normalized, name):
                hits_by_id.setdefault(
                    art_id_str,
                    ArtifactMetadata(name=name, id=art_id_str, type=art_type_str),
                )
                continue

            stored_readme = _extract_readme_text(item)
            if stored_readme and rx.search(stored_readme):
                hits_by_id.setdefault(
                    art_id_str,
                    ArtifactMetadata(name=name, id=art_id_str, type=art_type_str),
                )
                continue

            if (
                network_fetches < _MAX_NETWORK_README_FETCHES
                and isinstance(url, str)
                and (("github.com/" in url) or ("huggingface.co/" in url))
            ):
                network_fetches += 1
                readme = _readme_for_url(url)
                if readme and rx.search(readme):
                    hits_by_id.setdefault(
                        art_id_str,
                        ArtifactMetadata(name=name, id=art_id_str, type=art_type_str),
                    )

        last_key = resp.get("LastEvaluatedKey")
        if not last_key:
            break
        scan_kwargs["ExclusiveStartKey"] = last_key

    if not hits_by_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No artifact found under this regex.",
        )

    hits = sorted(hits_by_id.values(), key=lambda h: (h.name, h.id))
    return hits
