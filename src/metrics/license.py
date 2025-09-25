import base64
import requests
import os

"""
LicenseMetric module

This metric evaluates the quality of a project's license.
Scoring is based on recognized open-source licenses, with higher
scores awarded to permissive licenses, medium scores for copyleft
licenses, and lower scores for custom or unknown licenses.

Missing licenses receive a score of 0.0.
"""

from typing import Any, Dict, Optional
import time
from .protocol import Metric


# -------------------------------------------------------------------
# License scoring tiers
# These can be easily extended or modified as industry needs evolve.
# -------------------------------------------------------------------
HIGH_QUALITY_LICENSES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC"}

MEDIUM_QUALITY_LICENSES = {"GPL-3.0", "GPL-2.0", "LGPL-2.1", "LGPL-3.0", "MPL-2.0", "EPL-2.0"}

CUSTOM_LICENSE_KEYWORD = "Custom"
UNKNOWN_LICENSE = "Unknown"


class LicenseMetric(Metric):
    """
    Evaluate the quality of a repository's license.

    Attributes:
        score (float): Current score of the metric.
        latency (float): Time taken to compute the score in milliseconds.
    """

    def __init__(self) -> None:
        self.score: float = -1.0
        self.latency: float = -1.0

    def get_data(self, parsed_data: Dict[str, Any]) -> Optional[str]:
        # Direct license field (Hugging Face or metadata)
        license_value = parsed_data.get("license")
        if isinstance(license_value, str) and license_value.strip():
            return license_value.strip()

        url = parsed_data.get("url", "")
        if "github.com" in url:
            # Extract owner/repo
            parts = url.split("github.com/")[-1].split("/")
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                headers = {}
                token = os.getenv("GITHUB_TOKEN")
                if token:
                    headers["Authorization"] = f"token {token}"

                # Try license API
                resp = requests.get(
                    f"https://api.github.com/repos/{owner}/{repo}/license",
                    headers=headers,
                    timeout=5,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    spdx = data.get("license", {}).get("spdx_id")
                    if spdx and spdx != "NOASSERTION":
                        return spdx

                # Fallback: README scan
                resp = requests.get(
                    f"https://api.github.com/repos/{owner}/{repo}/readme",
                    headers=headers,
                    timeout=5,
                )
                if resp.status_code == 200:
                    readme_data = resp.json()
                    content = base64.b64decode(readme_data.get("content", "")).decode(
                        "utf-8", errors="ignore"
                    )
                    for lic in HIGH_QUALITY_LICENSES | MEDIUM_QUALITY_LICENSES:
                        if lic.lower().replace("-", " ") in content.lower():
                            return lic

        return None

    def calculate_score(self, data: Optional[str]) -> None:
        """
        Assign a quality score to the license.

        Scoring:
        - High-quality permissive licenses: 1.0
        - Medium-quality copyleft licenses: 0.7
        - Custom license: 0.5
        - Unknown license: 0.2
        - Missing license: 0.0

        Args:
            data (Optional[str]): The license string.
        """
        if not data:
            # Missing license
            self.score = 0.0
            return

        if data in HIGH_QUALITY_LICENSES:
            self.score = 1.0
        elif data in MEDIUM_QUALITY_LICENSES:
            self.score = 0.7
        elif CUSTOM_LICENSE_KEYWORD.lower() in data.lower():
            self.score = 0.5
        elif data == UNKNOWN_LICENSE:
            self.score = 0.2
        else:
            # Fallback for unrecognized licenses
            self.score = 0.2

    def process_score(self, parsed_data: Dict[str, Any]) -> None:
        """
        Process the license metric: extract data, compute score, and measure latency.

        Args:
            parsed_data (Dict[str, Any]): Parsed repository metadata.
        """
        start_time = time.perf_counter()
        data = self.get_data(parsed_data)
        self.calculate_score(data)
        end_time = time.perf_counter()

        self.latency = (end_time - start_time) * 1000.0  # milliseconds

    def get_score(self) -> float:
        """
        Get the latest computed score.

        Returns:
            float: The license quality score.
        """
        return self.score

    def get_latency(self) -> float:
        """
        Get the time taken to compute the score.

        Returns:
            float: Latency in milliseconds.
        """
        return self.latency
