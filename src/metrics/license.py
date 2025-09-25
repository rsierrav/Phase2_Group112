import base64
import requests
import os
import time
from typing import Any, Dict, Optional
from .protocol import Metric

# -------------------------------------------------------------------
# License scoring tiers (normalized to lowercase SPDX IDs)
# -------------------------------------------------------------------
HIGH_QUALITY_LICENSES = {"mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause", "isc"}
MEDIUM_QUALITY_LICENSES = {"gpl-3.0", "gpl-2.0", "lgpl-2.1", "lgpl-3.0", "mpl-2.0", "epl-2.0"}

CUSTOM_LICENSE_KEYWORD = "custom"
UNKNOWN_LICENSE = "unknown"


class LicenseMetric(Metric):
    """Evaluate the quality of a repository's license."""

    def __init__(self) -> None:
        self.score: float = -1.0
        self.latency: float = -1.0

    def get_data(self, parsed_data: Dict[str, Any]) -> Optional[str]:
        # Direct license field (Hugging Face or GitHub metadata)
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
                try:
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
                except Exception:
                    pass

                # If not there, check README
                try:
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
                            if lic.replace("-", " ") in content.lower():
                                return lic
                except Exception:
                    pass

        return None

    def calculate_score(self, data: Optional[str]) -> None:
        """Assign a quality score to the license."""
        if not data:
            self.score = 0.0
            return

        norm = data.strip().lower()

        if norm in HIGH_QUALITY_LICENSES:
            self.score = 1.0
        elif norm in MEDIUM_QUALITY_LICENSES:
            self.score = 0.7
        elif CUSTOM_LICENSE_KEYWORD in norm:
            self.score = 0.5
        elif norm == UNKNOWN_LICENSE:
            self.score = 0.2
        else:
            # Fallback for unrecognized licenses
            self.score = 0.2

    def process_score(self, parsed_data: Dict[str, Any]) -> None:
        start_time = time.perf_counter()
        data = self.get_data(parsed_data)
        self.calculate_score(data)
        end_time = time.perf_counter()
        self.latency = (end_time - start_time) * 1000.0

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> float:
        return self.latency
