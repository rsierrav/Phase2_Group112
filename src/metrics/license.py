import base64
import requests
import os
import time
import logging
from typing import Any, Dict, Optional
from .protocol import Metric

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
        license_value = parsed_data.get("license")
        if isinstance(license_value, str) and license_value.strip():
            logging.debug(f"License found directly in parsed_data: {license_value}")
            return license_value.strip()

        url = parsed_data.get("url", "")
        if "github.com" in url:
            parts = url.split("github.com/")[-1].split("/")
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                headers = {}
                token = os.getenv("GITHUB_TOKEN")
                if token:
                    headers["Authorization"] = f"token {token}"

                try:
                    logging.info(f"Querying GitHub license API for {owner}/{repo}")
                    resp = requests.get(
                        f"https://api.github.com/repos/{owner}/{repo}/license",
                        headers=headers,
                        timeout=5,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        spdx = data.get("license", {}).get("spdx_id")
                        if spdx and spdx != "NOASSERTION":
                            logging.debug(f"SPDX license detected: {spdx}")
                            return spdx
                except Exception as e:
                    logging.error(f"Error fetching license API for {owner}/{repo}: {e}")

                try:
                    logging.info(f"Checking README for license keywords in {owner}/{repo}")
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
                                logging.debug(f"License keyword found in README: {lic}")
                                return lic
                except Exception as e:
                    logging.error(f"Error scanning README for {owner}/{repo}: {e}")

        logging.warning("No license detected")
        return None

    def calculate_score(self, data: Optional[str]) -> None:
        if not data:
            self.score = 0.0
            logging.info("License missing -> score=0.0")
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
            self.score = 0.2

        logging.info(f"Calculated license score={self.score:.2f} for license='{data}'")

    def process_score(self, parsed_data: Dict[str, Any]) -> None:
        start_time = time.perf_counter()
        data = self.get_data(parsed_data)
        self.calculate_score(data)
        end_time = time.perf_counter()
        self.latency = (end_time - start_time) * 1000.0
        logging.debug(f"License metric latency={self.latency:.2f} ms")

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> float:
        return self.latency
