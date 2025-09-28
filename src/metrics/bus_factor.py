import os
import re
import time
import requests
import logging
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

        url = url.split("#")[0].split("?")[0].rstrip("/")
        m = re.search(r"github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", url)
        if m:
            repo = m.group(1)
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
            logging.info(f"Fetching commit authors from GitHub for {repo_path}")
            resp = requests.get(url, headers=self._make_headers(), timeout=10)
            if resp.status_code != 200:
                logging.warning(f"GitHub API returned {resp.status_code} for {repo_path}")
                return []
            commits = resp.json()
            authors: List[str] = []
            for c in commits:
                if isinstance(c.get("author"), dict) and c["author"] and c["author"].get("login"):
                    authors.append(str(c["author"]["login"]))
                    continue
                commit_info = c.get("commit", {}).get("author", {})
                name = commit_info.get("name")
                email = commit_info.get("email")
                if name:
                    authors.append(str(name))
                elif email:
                    authors.append(str(email))
            logging.debug(f"Fetched {len(authors)} commit authors for {repo_path}")
            return authors
        except Exception as e:
            logging.error(f"Error fetching commit authors for {repo_path}: {e}", exc_info=True)
            return []

    def get_data(self, parsed_data: Dict[str, Any]) -> List[str]:
        """
        Extract or Fetch a list of commit authors for linked repository.
        """
        pre_authors = parsed_data.get("commit_authors")
        if isinstance(pre_authors, list) and pre_authors:
            logging.debug("Using pre-fetched commit authors")
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

        code_url = parsed_data.get("code_url") or parsed_data.get("url")
        repo_path = self._extract_repo_path(code_url) if isinstance(code_url, str) else None
        if not repo_path:
            logging.warning("No valid repo path found for bus factor metric")
            return []

        authors = self._fetch_commit_authors_from_github(repo_path, per_page=100)
        seen: Set[str] = set()
        unique_authors: List[str] = []
        for a in authors:
            key = str(a).strip()
            if key and key not in seen:
                seen.add(key)
                unique_authors.append(key)

        logging.info(f"Unique authors found: {len(unique_authors)} for {repo_path}")
        return unique_authors

    def calculate_score(self, data: Any) -> None:
        """
        data: expected to be List[str] of author identifiers.
        """
        authors = []
        if isinstance(data, list):
            authors = [str(a).strip() for a in data if a]
        else:
            try:
                authors = [str(data)]
            except Exception:
                authors = []

        unique_count = len(set(authors))
        if unique_count <= 0:
            self.score = 0.0
        else:
            self.score = min(1.0, unique_count / 50.0)

        logging.info(f"Calculated bus factor score={self.score:.2f} (unique_count={unique_count})")

    def process_score(self, parsed_data: Dict[str, Any]) -> None:
        """
        Process the metric: measure latency and compute score.
        """
        start_time = time.perf_counter()
        data = self.get_data(parsed_data)
        self.calculate_score(data)
        end_time = time.perf_counter()
        self.latency = (end_time - start_time) * 1000
        logging.debug(f"Bus factor latency={self.latency:.2f} ms")

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> float:
        return self.latency
