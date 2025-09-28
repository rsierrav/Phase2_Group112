import os
import time
import logging
from typing import Any, Dict, List, Optional
import requests
from .protocol import Metric

# GitHub trees API to list repository files
GH_TREE_API = "https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"


class code_quality(Metric):
    def __init__(self):
        self.score: float = -1.0
        self.latency: float = -1.0

    def _make_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
        return headers

    def _fetch_repo_tree(self, repo_path: str, branch: str = "HEAD") -> Optional[List[Dict[str, Any]]]:
        url = GH_TREE_API.format(repo=repo_path, branch=branch)
        try:
            logging.info(f"Fetching repo tree for {repo_path}")
            resp = requests.get(url, headers=self._make_headers(), timeout=10)
            if resp.status_code == 200:
                payload = resp.json()
                logging.debug(f"Repo tree fetched with {len(payload.get('tree', []))} items")
                return payload.get("tree", [])
            logging.warning(f"GitHub API returned {resp.status_code} for repo tree {repo_path}")
            return None
        except Exception as e:
            logging.error(f"Error fetching repo tree for {repo_path}: {e}", exc_info=True)
            return None

    def get_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract repository evidence from CODE entry,
        or from MODEL entry with a code_url.
        """
        category = parsed_data.get("category", "")
        url = parsed_data.get("url", "")
        code_url = parsed_data.get("code_url", "")

        # Determine if we have a GitHub repo to check
        repo_url = None
        if category == "CODE" and "github.com" in url:
            repo_url = url
        elif category == "MODEL" and code_url and "github.com" in code_url:
            repo_url = code_url

        if not repo_url:
            logging.info("No GitHub repo found for code quality metric")
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
            parts = repo_url.split("github.com/")[-1].split("/")
            repo_path = "/".join(parts[:2])  # owner/repo
        except Exception:
            logging.error(f"Could not parse repo URL: {repo_url}")
            return {
                "has_tests": False,
                "has_ci": False,
                "has_lint_config": False,
                "python_file_count": 0,
                "has_readme": False,
                "has_packaging": False,
            }

        tree = self._fetch_repo_tree(repo_path)
        if not tree:
            logging.warning(f"No repo tree returned for {repo_path}")
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

            if (
                path.startswith("tests/")
                or "/tests/" in path
                or path.startswith("test/")
                or "/test/" in path
                or path.startswith("test_")
                or "/test_" in path
                or "testing/" in path
                or "/testing/" in path
                or path.endswith("_test.py")
                or path.endswith("test.py")
                or "unittest" in path
                or "pytest" in path
            ):
                has_tests = True

            if (
                path.startswith(".github/workflows")
                or path.endswith(".travis.yml")
                or path.endswith("travis.yml")
                or ".circleci/" in path
                or path.endswith("azure-pipelines.yml")
                or path.endswith("azure-pipelines.yaml")
                or path.endswith("jenkinsfile")
                or path.endswith(".yml")
                and ("ci" in path or "build" in path or "deploy" in path)
                or path.endswith(".yaml")
                and ("ci" in path or "build" in path or "deploy" in path)
                or path.startswith("ci/")
                or "/ci/" in path
                or path == "makefile"
                or path == "dockerfile"
                or path.endswith("build.sh")
                or path.endswith("build.py")
            ):
                has_ci = True

            if (
                path
                in {
                    ".flake8",
                    "pyproject.toml",
                    "setup.cfg",
                    "tox.ini",
                    ".pylintrc",
                    "pylint.cfg",
                    ".black",
                    ".isort.cfg",
                    ".pre-commit-config.yaml",
                    ".pre-commit-config.yml",
                    "requirements-dev.txt",
                    "requirements.dev.txt",
                }
                or path.endswith("lint.py")
                or path.endswith("format.py")
                or "linting" in path
                or "formatting" in path
            ):
                has_lint_config = True

            if path.startswith("readme") or path in {"readme.md", "readme.rst", "readme.txt", "readme"} or path == "index.md" or path == "home.md":
                has_readme = True

            if (
                path
                in {
                    "setup.py",
                    "pyproject.toml",
                    "setup.cfg",
                    "requirements.txt",
                    "pipfile",
                    "poetry.lock",
                    "conda.yml",
                    "environment.yml",
                    "manifest.in",
                    "__init__.py",
                }
                or path.startswith("requirements")
                and path.endswith(".txt")
                or "/setup.py" in path
                or "/pyproject.toml" in path
            ):
                has_packaging = True

            if path.endswith(".py"):
                python_file_count += 1

        logging.debug(
            f"Repo analysis: tests={has_tests}, ci={has_ci}, lint={has_lint_config}, "
            f"readme={has_readme}, packaging={has_packaging}, py_files={python_file_count}"
        )

        return {
            "has_tests": has_tests,
            "has_ci": has_ci,
            "has_lint_config": has_lint_config,
            "python_file_count": python_file_count,
            "has_readme": has_readme,
            "has_packaging": has_packaging,
        }

    def calculate_score(self, data: Any) -> None:
        start = time.perf_counter()

        has_tests = bool(data.get("has_tests", False))
        has_ci = bool(data.get("has_ci", False))
        has_lint = bool(data.get("has_lint_config", False))
        py_count = int(data.get("python_file_count", 0))
        has_readme = bool(data.get("has_readme", False))
        has_packaging = bool(data.get("has_packaging", False))

        w_tests, w_ci, w_lint, w_py, w_doc_pack = 0.30, 0.25, 0.15, 0.15, 0.15

        s_tests = 1.0 if has_tests else 0.0
        s_ci = 1.0 if has_ci else 0.0
        s_lint = 1.0 if has_lint else 0.0
        s_py = min(1.0, py_count / 20.0) if py_count > 0 else 0.0

        if has_readme and has_packaging:
            s_doc_pack = 1.0
        elif has_readme or has_packaging:
            s_doc_pack = 0.5
        else:
            s_doc_pack = 0.0

        score = w_tests * s_tests + w_ci * s_ci + w_lint * s_lint + w_py * s_py + w_doc_pack * s_doc_pack

        self.score = max(0.0, min(1.0, score))

        end = time.perf_counter()
        self.latency = (end - start) * 1000.0

        logging.info(f"Code quality score={self.score:.2f}, latency={self.latency:.2f} ms")

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> float:
        return self.latency
