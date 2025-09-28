import os
import re
import time
import requests
from typing import Dict, Any, List, Set, Optional
from .protocol import Metric

# GitHub commits API template. We'll request a page of commits (per_page up to 100).
GH_COMMITS_API = "https://api.github.com/repos/{repo}/commits?per_page={per_page}"


class bus_factor(Metric):
    def __init__(self):
        self.score: float = -1.0
        self.latency: float = -1.0

    def _make_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
        return headers

    def _extract_repo_path(self, url: str) -> Optional[str]:
        """
        Given a GitHub URL like:
        https://github.com/owner/repo
        or variations with extra path parts, return "owner/repo" or None.
        """
        if not url or "github.com" not in url:
            return None

        # remove tailing slashes and common fragments
        url = url.split("#")[0].split("?")[0].rstrip("/")

        # regex to capture owner/repo
        m = re.search(r"github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", url)
        if m:
            # return the first two path components only (owner/repo)
            repo = m.group(1)
            # sanitize (strip any tailing path components)
            parts = repo.split("/")
            if len(parts) >= 2:
                return f"{parts[0]}/{parts[1]}"
        return None

    def _fetch_commit_authors_from_github(self, repo_path: str, per_page: int = 100) -> List[str]:
        """
        Fetch recent commits from GitHub and return a list of author identifiers.
        This function returns a list possibly with duplicates.
        """
        try:
            url = GH_COMMITS_API.format(repo=repo_path, per_page=per_page)
            resp = requests.get(url, headers=self._make_headers(), timeout=10)
            if resp.status_code != 200:
                # Non-200: return empty list (caller will handle)
                return []
            commits = resp.json()
            authors: List[str] = []
            for c in commits:
                # Prefer the GitHub user login if available
                if isinstance(c.get("author"), dict) and c["author"] and c["author"].get("login"):
                    authors.append(str(c["author"]["login"]))
                    continue

                # Otherwise fall back to commit.author.name or email
                commit_info = c.get("commit", {}).get("author", {})
                name = commit_info.get("name")
                email = commit_info.get("email")
                if name:
                    authors.append(str(name))
                elif email:
                    authors.append(str(email))
            return authors
        except Exception:
            # Any exception (network, JSON decode, etc.) -> return empty to avoid crashing
            return []

    def get_data(self, parsed_data: Dict[str, Any]) -> List[str]:
        """
        Extract or Fetch a list of commit authors for linked repository.
        Priority:
        1. if parsed_data already contains 'commit_authors' (a list), return it.
        2. if parsed_data contains 'code_url' pointing to github, extract
        owner/repo and call the GitHub commits API to retrieve recent commit authors.
        3. otherwise return empty list.

        Returns list[str] (possibly empty).
        """
        # 1) Use pre-fetched commit authors if available
        pre_authors = parsed_data.get("commit_authors")
        if isinstance(pre_authors, list) and pre_authors:
            seen = set()
            normalized = []
            for a in pre_authors:
                if not a:
                    continue
                name = str(a).strip()
                if name not in seen:
                    seen.add(name)
                    normalized.append(name)
            return normalized

        # 2) Use code_url from parsed_data (parse_input.py now populates 'code_url' where possible)
        code_url = parsed_data.get("code_url") or parsed_data.get("url")  # fallback to entry url
        repo_path = self._extract_repo_path(code_url) if isinstance(code_url, str) else None
        if not repo_path:
            return []

        # 3) Fetch commit authors from GitHub
        authors = self._fetch_commit_authors_from_github(repo_path, per_page=100)
        # Normalize and deduplicate while preserving order
        seen: Set[str] = set()
        unique_authors: List[str] = []
        for a in authors:
            key = str(a).strip()
            if key and key not in seen:
                seen.add(key)
                unique_authors.append(key)

        return unique_authors

    def calculate_score(self, data: Any) -> None:
        """
        data: expected to be List[str] of author identifiers.
        Sets self.score in [0,1] and sets self.latency in milliseconds.
        Heuristic: score = min(1.0, unique_author_count / 50.0)
        """
        authors = []
        if isinstance(data, list):
            authors = [str(a).strip() for a in data if a]
        else:
            # Defensive: if something else was provided, attemto coerce to list
            try:
                authors = [str(data)]
            except Exception:
                authors = []

        unique_count = len(set(authors))

        # Simple linear scaling: 0 authors -> 0.0, 50+ -> 1.0
        if unique_count <= 0:
            self.score = 0.0
        else:
            self.score = min(1.0, unique_count / 50.0)

    def process_score(self, parsed_data: Dict[str, Any]) -> None:
        """
        Process the metric: measure latency and compute score.
        Updates `score` and `latency` attributes.
        """
        start_time = time.perf_counter()
        data = self.get_data(parsed_data)
        self.calculate_score(data)
        end_time = time.perf_counter()

        # store latency in milliseconds
        self.latency = (end_time - start_time) * 1000

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> float:
        # return latency in milliseconds
        return self.latency
