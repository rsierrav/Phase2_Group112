# src/metrics/license.py

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
        """
        Extract license information from parsed repository metadata.

        Args:
            parsed_data (Dict[str, Any]): The parsed metadata from the repo.

        Returns:
            Optional[str]: The license string if present, otherwise None.
        """
        license_value = parsed_data.get("license")
        if isinstance(license_value, str):
            return license_value.strip()
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
