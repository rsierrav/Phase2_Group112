# src/metrics/ramp_up_time.py
import time
import requests
import base64
import os
from typing import Dict, Any, Optional
from .protocol import Metric


class RampUpTime(Metric):
    """
    Evaluate how easy it is to get started with a model/dataset/code
    based on documentation quality, examples, and setup instructions.
    """

    def __init__(self):
        self.score: float = -1.0
        self.latency: float = -1.0

    def _make_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
        return headers

    def _get_readme_content(self, repo_path: str) -> Optional[str]:
        """Fetch README content from GitHub repo."""
        try:
            resp = requests.get(
                f"https://api.github.com/repos/{repo_path}/readme",
                headers=self._make_headers(),
                timeout=10,
            )
            if resp.status_code == 200:
                readme_data = resp.json()
                content = base64.b64decode(readme_data.get("content", "")).decode(
                    "utf-8", errors="ignore"
                )
                return content
        except Exception:
            pass
        return None

    def _get_hf_readme_content(self, model_id: str) -> Optional[str]:
        """Fetch README content from HuggingFace model/dataset."""
        try:
            resp = requests.get(f"https://huggingface.co/{model_id}/raw/main/README.md", timeout=10)
            if resp.status_code == 200:
                return resp.text
        except Exception:
            pass
        return None

    def get_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract documentation and setup information."""
        url = parsed_data.get("url", "")
        code_url = parsed_data.get("code_url", "")

        readme_content = ""
        has_examples = False
        has_installation = False
        has_quick_start = False
        has_code_snippets = False
        documentation_length = 0

        # Get README from HuggingFace
        if "huggingface.co" in url:
            try:
                if "/datasets/" in url:
                    model_id = "datasets/" + "/".join(
                        url.split("huggingface.co/datasets/")[-1].split("/")[:2]
                    )
                else:
                    model_id = "/".join(url.split("huggingface.co/")[-1].split("/")[:2])
                readme_content = self._get_hf_readme_content(model_id) or ""
            except Exception:
                pass

        # Get README from GitHub (code_url or direct GitHub URL)
        repo_path = None
        if "github.com" in url:
            try:
                parts = url.split("github.com/")[-1].split("/")
                repo_path = "/".join(parts[:2])
            except Exception:
                pass
        elif code_url and "github.com" in code_url:
            try:
                parts = code_url.split("github.com/")[-1].split("/")
                repo_path = "/".join(parts[:2])
            except Exception:
                pass

        if repo_path:
            github_readme = self._get_readme_content(repo_path) or ""
            readme_content = readme_content + "\n" + github_readme

        # Analyze README content
        if readme_content:
            readme_lower = readme_content.lower()
            documentation_length = len(readme_content)

            # Check for examples
            example_indicators = [
                "example",
                "examples",
                "usage",
                "how to use",
                "quick start",
                "getting started",
                "tutorial",
                "demo",
                "```python",
                "```py",
            ]
            has_examples = any(indicator in readme_lower for indicator in example_indicators)

            # Check for installation instructions
            install_indicators = [
                "install",
                "pip install",
                "conda install",
                "npm install",
                "setup",
                "requirements",
                "dependencies",
            ]
            has_installation = any(indicator in readme_lower for indicator in install_indicators)

            # Check for quick start guide
            quickstart_indicators = [
                "quick start",
                "quickstart",
                "getting started",
                "basic usage",
                "simple example",
                "minimal example",
            ]
            has_quick_start = any(indicator in readme_lower for indicator in quickstart_indicators)

            # Check for code snippets
            has_code_snippets = "```" in readme_content or "from " in readme_content

        # Check HuggingFace widget data (interactive examples)
        widget_data = parsed_data.get("metadata", {}).get("widgetData", [])
        if widget_data:
            has_examples = True

        return {
            "documentation_length": documentation_length,
            "has_examples": has_examples,
            "has_installation": has_installation,
            "has_quick_start": has_quick_start,
            "has_code_snippets": has_code_snippets,
            "readme_content": readme_content[:500],  # First 500 chars for debugging
        }

    def calculate_score(self, data: Dict[str, Any]) -> None:
        """Calculate ramp-up time score based on documentation quality."""
        start = time.perf_counter()

        score = 0.0

        # Documentation length contribution (0-0.3)
        doc_length = data.get("documentation_length", 0)
        if doc_length > 2000:
            score += 0.3
        elif doc_length > 1000:
            score += 0.25
        elif doc_length > 500:
            score += 0.2
        elif doc_length > 200:
            score += 0.15
        elif doc_length > 100:
            score += 0.1

        # Examples contribution (0-0.25)
        if data.get("has_examples", False):
            score += 0.25

        # Installation instructions (0-0.2)
        if data.get("has_installation", False):
            score += 0.2

        # Quick start guide (0-0.15)
        if data.get("has_quick_start", False):
            score += 0.15

        # Code snippets (0-0.1)
        if data.get("has_code_snippets", False):
            score += 0.1

        self.score = min(1.0, score)

        end = time.perf_counter()
        self.latency = (end - start) * 1000.0

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> float:
        return self.latency
