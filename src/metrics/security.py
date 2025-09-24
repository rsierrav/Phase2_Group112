# src/metrics/security.py
import requests
import time
from typing import Any, Dict
from .protocol import Metric


class SecurityMetric(Metric):
    """
    SecurityMetric evaluates whether a project has basic security practices:
    - Presence of SECURITY.md
    - Dependency files (requirements.txt, environment.yml)
    - Dependabot/.github configs
    - HuggingFace security-related tags
    """

    def __init__(self):
        self.score: float = 0.0
        self.latency: float = 0.0

    def get_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        url = parsed_data.get("url", "")
        category = parsed_data.get("category", "")
        data: Dict[str, Any] = {
            "url": url,
            "category": category,
            "metadata": parsed_data.get("metadata", {}),
        }

        if category == "CODE" and "github.com" in url:
            parts = url.split("github.com/")[-1].split("/")
            if len(parts) >= 2:
                repo_path = "/".join(parts[:2])
                api_url = f"https://api.github.com/repos/{repo_path}/contents/"
                try:
                    resp = requests.get(api_url, timeout=10)
                    if resp.status_code == 200:
                        data["files"] = [f["name"].lower() for f in resp.json() if "name" in f]
                except Exception as e:
                    data["error"] = str(e)

        return data

    def calculate_score(self, data: Dict[str, Any]) -> None:
        score = 0.0
        url = data.get("url", "")

        # GitHub security practices
        files = data.get("files", [])
        if "security.md" in files:
            score += 0.5
        if "requirements.txt" in files or "environment.yml" in files:
            score += 0.25
        if ".github" in files:
            score += 0.25

        # HuggingFace tags mentioning security
        if "huggingface.co" in url:
            metadata = data.get("metadata", {})
            if "cardData" in metadata and "tags" in metadata["cardData"]:
                tags = metadata["cardData"]["tags"]
                if any("security" in t.lower() for t in tags):
                    score += 0.5

        self.score = min(1.0, score)

    def process_score(self, parsed_data: Dict[str, Any]) -> None:
        start = time.perf_counter()
        data = self.get_data(parsed_data)
        self.calculate_score(data)
        end = time.perf_counter()
        self.latency = (end - start) * 1000

    def get_score(self) -> float:
        return getattr(self, "score", 0.0)

    def get_latency(self) -> float:
        return getattr(self, "latency", 0.0)
