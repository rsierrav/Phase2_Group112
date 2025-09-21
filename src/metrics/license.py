# src/metrics/license.py

from typing import Any, Dict
import time
from .protocol import Metric


class LicenseMetric(Metric):
    def __init__(self):
        self.score: float = 0.0
        self.latency: float = 0.0

    def get_data(self, parsed_data: Dict[str, Any]) -> Any:
        """
        Extract license information from parsed repo data.
        """
        return parsed_data.get("license")

    def calculate_score(self, data: Any) -> None:
        """
        Assign score based on license quality tiers.
        """
        if data is None or data == "":
            # Missing license
            self.score = 0.0
            return

        # High-quality, permissive licenses
        high_quality = {
            "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC"
        }

        # Medium-quality, copyleft or restrictive
        medium_quality = {
            "GPL-3.0", "GPL-2.0",
            "LGPL-2.1", "LGPL-3.0",
            "MPL-2.0", "EPL-2.0"
        }

        if data in high_quality:
            self.score = 1.0
        elif data in medium_quality:
            self.score = 0.7
        elif isinstance(data, str) and "Custom" in data:
            self.score = 0.5
        elif data == "Unknown":
            self.score = 0.2
        else:
            # Any unrecognized license falls here
            self.score = 0.2

    def process_score(self, parsed_data: Dict[str, Any]) -> None:
        """
        Measure latency and compute score.
        """
        start_time = time.perf_counter()
        data = self.get_data(parsed_data)
        self.calculate_score(data)
        end_time = time.perf_counter()

        self.latency = (end_time - start_time) * 1000  # ms

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> float:
        return self.latency
