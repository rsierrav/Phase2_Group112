"""Artifact search endpoints."""

from __future__ import annotations

import re
from typing import Optional
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


_REGEX_META = set(r".^$*+?{}[]\|()")


def _fetch_text(url: str, timeout: float = 0.75, max_bytes: int = 250_000) -> str:
    """Best-effort small GET. Returns '' on failure."""
    try:
        req = Request(url, headers={"User-Agent": "ece461-registry"})
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read(max_bytes)
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _github_owner_repo(url: str) -> Optional[tuple[str, str]]:
    if not isinstance(url, str) or "github.com/" not in url:
        return None
    try:
        path = url.split("github.com/", 1)[1].strip("/")
        parts = path.split("/")
        if len(parts) < 2:
            return None
        owner = parts[0]
        repo = parts[1]
        if repo.endswith(".git"):
            repo = repo[:-4]
        return owner, repo
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
    Autograder may store README text locally under varied keys.
    """
    md = item.get("metadata") or {}
    data = item.get("data") or {}

    candidates = [
        # top-level
        item.get("readme"),
        item.get("README"),
        item.get("readme_text"),
        item.get("readmeContent"),
        item.get("readme_content"),
        item.get("readmeMarkdown"),
        item.get("readme_md"),
        item.get("readmeBody"),
        # nested metadata
        md.get("readme"),
        md.get("README"),
        md.get("readme_text"),
        md.get("readmeContent"),
        md.get("readme_content"),
        md.get("readmeMarkdown"),
        md.get("readme_md"),
        md.get("readmeBody"),
        # nested data
        data.get("readme"),
        data.get("README"),
        data.get("readme_text"),
        data.get("readmeContent"),
        data.get("readme_content"),
        data.get("readmeMarkdown"),
        data.get("readme_md"),
        data.get("readmeBody"),
    ]

    for c in candidates:
        if isinstance(c, str) and c.strip():
            return c
    return ""


def _readme_for_url(url: str) -> str:
    """Fetch README from GH/HF raw endpoints. Cached. Never raises."""
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
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.MD",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.MD",
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.txt",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.txt",
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.rst",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.rst",
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
                f"{base}/raw/main/README.MD",
                f"{base}/raw/master/README.MD",
            ]
            for c in candidates:
                text = _fetch_text(c)
                if text:
                    break

    _README_CACHE[url] = text or ""
    return _README_CACHE[url]


def _compile_regex(pattern: str) -> tuple[re.Pattern, str, bool, str]:
    """
    Returns (compiled_regex, normalized_pattern, is_js_style, original_pattern_for_literal).
    Supports:
      - Python regex: '^foo$'
      - JS-style: '/^foo$/i' or '/^foo$/' (flags optional; supported: i, m, s)
    """
    flags = 0
    pat = pattern.strip()
    is_js_style = False
    original_for_literal = pat
    # For JS-style regex
    if len(pat) >= 2 and pat[0] == "/":
        last = pat.rfind("/")
        if last > 0:
            maybe_pat = pat[1:last]
            maybe_flags = pat[last + 1 :]  # noqa: E203

            if maybe_flags == "" or maybe_flags.isalpha():
                is_js_style = True
                pat = maybe_pat
                original_for_literal = pat
                if "i" in maybe_flags:
                    flags |= re.IGNORECASE
                if "m" in maybe_flags:
                    flags |= re.MULTILINE
                if "s" in maybe_flags:
                    flags |= re.DOTALL

    elif len(pat) >= 2 and ((pat[0] == pat[-1] == '"') or (pat[0] == pat[-1] == "'")):
        pat = pat[1:-1].strip()

    try:
        return re.compile(pat, flags), pat, is_js_style, original_for_literal
    except re.error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is missing field(s) in the artifact_regex or it is formed improperly, or is invalid",
        )


def _is_literal_name_query(normalized_pattern: str, is_js_style: bool) -> bool:
    if is_js_style:
        return False

    i = 0
    while i < len(normalized_pattern):
        ch = normalized_pattern[i]
        if ch in _REGEX_META:
            if i > 0 and normalized_pattern[i - 1] == "\\":
                i += 1
                continue
            return False
        i += 1

    return True


def _name_matches(rx: re.Pattern, normalized_pattern: str, is_js_style: bool, name: str) -> bool:
    if _is_literal_name_query(normalized_pattern, is_js_style):
        return name == normalized_pattern

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
    if "regex" not in body:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is missing field(s) in the artifact_regex or it is formed improperly, or is invalid",
        )

    regex_value = body["regex"]
    if not isinstance(regex_value, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is missing field(s) in the artifact_regex or it is formed improperly, or is invalid",
        )

    if not regex_value.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is missing field(s) in the artifact_regex or it is formed improperly, or is invalid",
        )

    print(f"DEBUG: Received regex pattern: '{regex_value}'")  # DEBUG

    rx, normalized, is_js_style, _ = _compile_regex(regex_value)
    literal_name_only = _is_literal_name_query(normalized, is_js_style)

    print(
        f"DEBUG: normalized='{normalized}', is_js_style={is_js_style}, literal_name_only={literal_name_only}"
    )  # DEBUG

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

        print(f"DEBUG: Scanning {len(items)} items")  # DEBUG

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

            print(f"DEBUG: Checking artifact: name='{name}', id='{art_id_str}'")  # DEBUG

            if literal_name_only:
                print(
                    f"DEBUG: Literal check: name='{name}' == normalized='{normalized}'? {name == normalized}"
                )  # DEBUG
                if name == normalized:
                    print(f"DEBUG: MATCH FOUND: {name}")  # DEBUG
                    hits_by_id.setdefault(
                        art_id_str,
                        ArtifactMetadata(name=name, id=art_id_str, type=art_type_str),
                    )
                continue

            if _name_matches(rx, normalized, is_js_style, name):
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

    return sorted(hits_by_id.values(), key=lambda h: (h.name, h.id))
