import time
import requests
from typing import Dict, Any, List, Set
from .protocol import Metric

GH_COMMITS_API = "https://api.github.com/repos/{repo}/commits"


class bus_factor(Metric):
    def __init__(self):
        self.score: float = 0.0
        self.latency_ms: int = 0

    def get_data(self, parsed_data: Dict[str, Any]) -> List[str]:
        """
        For code repos (GitHub), fetch recent commits and extract unique authors.
        Return a list of author identifiers (names or emails).
        """
        category = parsed_data.get("category", "")
        url = parsed_data.get("url", "")

        if category != "CODE" or "github.com" not in url:
            return []

        # Extract owner/repo from URL
        try:
            parts = url.split("github.com/")[-1].split("/")
            repo_path = "/".join(parts[:2])  # owner/repo
        except Exception:
            return []

        authors: Set[str] = set()
        try:
            # Limit to first 30 commits (default GitHub API pagination)
            resp = requests.get(GH_COMMITS_API.format(repo=repo_path), timeout=10)
            if resp.status_code == 200:
                commits = resp.json()
                for c in commits:
                    commit_info = c.get("commit", {}).get("author", {})
                    name = commit_info.get("name")
                    email = commit_info.get("email")
                    if name:
                        authors.add(name)
                    elif email:
                        authors.add(email)
        except Exception:
            # Fail siltently, return empty authors
            return []

        return list(authors)

    def calculate_score(self, data: Any) -> None:
        start = time.perf_counter()

        # Ensure data is a list of strings
        authors: Set[str] = set(str(a).strip() for a in data if a)

        # Simple heuristic: more unique authors -> higher bus factor
        # 5 or more unique authors gives a full score of 1.0
        count = len(authors)
        self.score = min(1.0, count / 5.0)

        end = time.perf_counter()
        self.latency_ms = int(round((end - start) * 1000))

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> int:
        # return latency in milliseconds
        return self.latency_ms
