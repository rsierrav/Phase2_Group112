# src/metrics/bus_factor.py
import time
import requests
import os
from typing import Dict, Any, List, Set
from .protocol import Metric

GH_COMMITS_API = "https://api.github.com/repos/{repo}/commits"


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

    def get_data(self, parsed_data: Dict[str, Any]) -> List[str]:
        """
        For any entry with a code_url (GitHub), fetch recent commits and extract unique authors.
        Return a list of author identifiers (names or emails).
        """
        category = parsed_data.get("category", "")
        url = parsed_data.get("url", "")
        code_url = parsed_data.get("code_url", "")

        # Check if we have a GitHub repo to analyze
        repo_url = None
        if category == "CODE" and "github.com" in url:
            repo_url = url
        elif code_url and "github.com" in code_url:
            repo_url = code_url

        if not repo_url:
            return []

        # Extract owner/repo from URL
        try:
            parts = repo_url.split("github.com/")[-1].split("/")
            repo_path = "/".join(parts[:2])  # owner/repo
        except Exception:
            return []

        authors: Set[str] = set()
        try:
            # Get commits with authentication
            resp = requests.get(
                GH_COMMITS_API.format(repo=repo_path), headers=self._make_headers(), timeout=10
            )
            if resp.status_code == 200:
                commits = resp.json()
                for c in commits:
                    commit_info = c.get("commit", {}).get("author", {})
                    name = commit_info.get("name")
                    email = commit_info.get("email")
                    if name and name not in ["GitHub", "github-actions[bot]"]:
                        authors.add(name)
                    elif email and email not in ["noreply@github.com"]:
                        authors.add(email)
        except Exception:
            # Fail silently, return empty authors
            return []

        return list(authors)

    def calculate_score(self, data: Any) -> None:
        start = time.perf_counter()

        # Ensure data is a list of strings
        authors: Set[str] = set(str(a).strip() for a in data if a)

        # Improved heuristic: more unique authors -> higher bus factor
        # 3 or more unique authors gives a full score of 1.0
        count = len(authors)
        if count >= 3:
            self.score = 1.0
        elif count == 2:
            self.score = 0.7
        elif count == 1:
            self.score = 0.4
        else:
            self.score = 0.0

        end = time.perf_counter()
        self.latency = (end - start) * 1000.0

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> float:
        return self.latency
