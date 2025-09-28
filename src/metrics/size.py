from typing import Any, Dict
import time
from .protocol import Metric


class SizeMetric(Metric):
    """
    Metric to evaluate model size compatibility with various hardware types.
    Produces both a dictionary of per-device scores and an overall average score.
    """

    def __init__(self):
        self.score: float = -1.0
        self.latency: float = -1.0
        self.size_score: Dict[str, float] = {}

    def get_data(self, parsed_data: Dict[str, Any]) -> int:
        return parsed_data.get("model_size_mb", 0)

    def calculate_score(self, size_mb: int) -> None:
        """
        Map model size (MB) into compatibility scores for different hardware.
        Scores are between 0.0 and 1.0.
        """
        # Handle zero size case
        if size_mb <= 0:
            self.size_score = {
                "raspberry_pi": 0.0,
                "jetson_nano": 0.0,
                "desktop_pc": 0.0,
                "aws_server": 0.0,
            }
            self.score = 0.0
            return

        # In MBs (approximate thresholds)
        thresholds = {
            "raspberry_pi": 50,
            "jetson_nano": 200,
            "desktop_pc": 2000,
            "aws_server": 10000,
        }

        scores = {}
        for device, max_size in thresholds.items():
            if size_mb <= max_size:
                # Linear scoring: smaller models get higher scores
                score = 1.0 - (size_mb / max_size) * 0.5  # Range from 1.0 to 0.5
            else:
                # Exponential penalty for oversized models
                overage_ratio = (size_mb - max_size) / max_size
                score = max(0.0, 0.5 * (1.0 / (1.0 + overage_ratio)))

            # Round to 2 decimal places to avoid floating point precision issues
            scores[device] = round(min(max(score, 0.0), 1.0), 2)

        self.size_score = scores
        # Overall score is the average
        self.score = round(sum(scores.values()) / len(scores), 2)

    def process_score(self, parsed_data: Dict[str, Any]) -> None:
        """Process the metric with timing."""
        start_time = time.perf_counter()
        data = self.get_data(parsed_data)
        self.calculate_score(data)
        end_time = time.perf_counter()
        self.latency = (end_time - start_time) * 1000

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> float:
        return self.latency

    def get_size_score(self) -> Dict[str, float]:
        """
        Return the dictionary of hardware compatibility scores.
        """
        return self.size_score
