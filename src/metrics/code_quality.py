import os
import time
from typing import Any, Dict, List, Optional
import requests
from .protocol import Metric

# GitHub trees API (recursive) to list respository files
GH_TREE_API = "https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"


class code_quality(Metric):
    def __init__(self):
        self.score: float = 0.0
        self.latency: float = 0.0
        self.weight: float = 0.0

    def _make_headers(self) -> Dict[str, str]:
        """
        Prepare headers for GitHub API requests. If GITHUB_TOKEN is set in
        environment, use it to increase rate limits.
        """
        headers: Dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
        return headers

    def _fetch_repo_tree(
        self, repo_path: str, branch: str = "HEAD"
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Returns the 'tree' list from GitHub git/trees response, or None on failure.
        """
        url = GH_TREE_API.format(repo=repo_path, branch=branch)
        try:
            resp = requests.get(url, headers=self._make_headers(), timeout=10)
            if resp.status_code == 200:
                payload = resp.json()
                # The tree field is usually present on success
                return payload.get("tree", [])
            else:
                # Non-200 -> return None so caller can handle gracefully
                return None
        except Exception:
            return None

    def get_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts repository file-list evidence and returns a small
        "inventory" dict that calculate_score can use.
        Keys returned:
          - has_tests: bool (presence of tests/ or test_*.py)
          - has_ci: bool (presence of .github/workflows/ or other CI files)
          - has_lint_config: bool (presence of .flake8 or pyproject.toml containing [tool.flake8])
          - python_file_count: int
          - has_readme: bool
          - has_packaging: bool (setup.py or pyproject.toml)
        If the entry is not a CODE GitHub URL, returns an "empty" dict (zeros/False).
        """
        category = parsed_data.get("category", "")
        url = parsed_data.get("url", "")

        # If not a GitHub CODE entry, return default "empty" results
        if category != "CODE" or "github.com" not in url:
            return {
                "has_tests": False,
                "has_ci": False,
                "has_lint_config": False,
                "python_file_count": 0,
                "has_readme": False,
                "has_packaging": False,
            }

        # Extract owner/repo
        try:
            parts = url.split("github.com/")[-1].split("/")
            repo_path = "/".join(parts[:2])  # owner/repo
        except Exception:
            return {
                "has_tests": False,
                "has_ci": False,
                "has_lint_config": False,
                "python_file_count": 0,
                "has_readme": False,
                "has_packaging": False,
            }

        tree = self._fetch_repo_tree(repo_path)
        # If tree fetch failed, return defaults (caller can still compute conservative score)
        if not tree:
            return {
                "has_tests": False,
                "has_ci": False,
                "has_lint_config": False,
                "python_file_count": 0,
                "has_readme": False,
                "has_packaging": False,
            }

        # Inspect file paths
        has_tests = False
        has_ci = False
        has_lint_config = False
        python_file_count = 0
        has_readme = False
        has_packaging = False

        for entry in tree:
            path = entry.get("path", "").lower()

            # tests presence
            if (
                path.startswith("tests/")
                or "/tests/" in path
                or path.startswith("test_")
                or "/test_" in path
            ):
                has_tests = True

            # CI presence (.github/workflows/ or common CI files)
            if (
                path.startswith(".github/workflows")
                or path.endswith(".travis.yml")
                or path.endswith("circleci/config.yml")
                or path.endswith("azure-pipelines.yml")
            ):
                has_ci = True

            # Lint config: .flake8 or pyproject.toml containing flake8
            # (we can only detect file presence here)
            if path == ".flake8" or path == "pyproject.toml":
                # If pyproject.toml is present we mark lint config as possibly present;
                # deeper inspection of file contents would be required for certainty.
                has_lint_config = True

            # README detection
            if path in {"readme.md", "readme.rst", "readme"}:
                has_readme = True

            # Packaging detection
            if path in {"setup.py", "pyproject.toml"}:
                has_packaging = True

            # Python files count
            if path.endswith(".py"):
                python_file_count += 1

        return {
            "has_tests": has_tests,
            "has_ci": has_ci,
            "has_lint_config": has_lint_config,
            "python_file_count": python_file_count,
            "has_readme": has_readme,
            "has_packaging": has_packaging,
        }

    def calculate_score(self, data: Any) -> None:
        """
        Compute a weighted score in [0,1] from the inventory returned by get_data.
        We measure latency only for the calculation itself (not for network calls made in get_data).
        Weights (example):
          - tests presence: 0.30
          - CI presence:    0.25
          - lint config:    0.15
          - python files:   0.15  (scaled: more py files -> indicates more code to check;
          >0 => partial credit)
          - readme/setup:   0.15
        """
        start = time.perf_counter()

        # Defensive defaults
        has_tests = bool(data.get("has_tests", False))
        has_ci = bool(data.get("has_ci", False))
        has_lint = bool(data.get("has_lint_config", False))
        py_count = int(data.get("python_file_count", 0))
        has_readme = bool(data.get("has_readme", False))
        has_packaging = bool(data.get("has_packaging", False))

        # Weights
        w_tests = 0.30
        w_ci = 0.25
        w_lint = 0.15
        w_py = 0.15
        w_doc_pack = 0.15

        # Subscores
        s_tests = 1.0 if has_tests else 0.0
        s_ci = 1.0 if has_ci else 0.0
        s_lint = 1.0 if has_lint else 0.0
        # For python files, give partial credit if there are any python files.
        # If many python files exist (>= 20), treat as full credit because codebase is non-trivial.
        if py_count <= 0:
            s_py = 0.0
        else:
            s_py = min(1.0, py_count / 20.0)

        s_doc_pack = 0.0
        # presence of either README or packaging config gives partial/full credit
        if has_readme and has_packaging:
            s_doc_pack = 1.0
        elif has_readme or has_packaging:
            s_doc_pack = 0.5
        else:
            s_doc_pack = 0.0

        # Weighted sum
        score = (
            w_tests * s_tests
            + w_ci * s_ci
            + w_lint * s_lint
            + w_py * s_py
            + w_doc_pack * s_doc_pack
        )

        # Ensure normalized
        self.score = max(0.0, min(1.0, score))

        end = time.perf_counter()
        self.latency_ms = int(round((end - start) * 1000))

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> int:
        return self.latency_ms
