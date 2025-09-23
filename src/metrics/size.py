# Tristan
# src/metrics/size.py

from typing import Any, Dict
from .protocol import Metric


class SizeMetric(Metric):
    """
    Metric to evaluate model size compatibility with various hardware types.
    Produces both a dictionary of per-device scores and an overall average score.
    """

    def __init__(self):
        self.score: float = 0.0
        self.latency: float = 0.0
        self.size_score: Dict[str, float] = {}
        self.weight: float = 0.0

    def get_data(self, parsed_data: Dict[str, Any]) -> int:
        """
        Expect parsed_data to include model size in megabytes (MB).
        """
        return parsed_data.get("model_size_mb", 0)

    def calculate_score(self, size_mb: int) -> None:
        """
        Map model size (MB) into compatibility scores for different hardware.
        Scores are between 0.0 and 1.0.
        """

        # In MBs (approximate thresholds)
        thresholds = {
            "raspberry_pi": 50,  # above this, performance drops
            "jetson_nano": 200,
            "desktop_pc": 2000,
            "aws_server": 10000,
        }

        scores = {}
        for device, max_size in thresholds.items():
            if size_mb <= max_size:
                # smaller models get slightly higher scores
                score = 0.5 + 0.5 * (1 - size_mb / max_size)
            else:
                # penalize oversize models quickly
                score = max(0.0, 1.0 - (size_mb - max_size) / (2 * max_size))
            scores[device] = round(score, 2)

        self.size_score = scores
        # Overall score is the average
        self.score = sum(scores.values()) / len(scores)

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> float:
        return self.latency

    def get_size_score(self) -> Dict[str, float]:
        """
        Return the dictionary of hardware compatibility scores.
        """
        return self.size_score
