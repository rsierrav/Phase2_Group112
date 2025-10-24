# src/metrics/size.py
from typing import Any, Dict
import time
import logging
from .protocol import Metric


class SizeMetric(Metric):
    """Evaluate model size compatibility with hardware devices."""

    def __init__(self):
        self.score: float = -1.0
        self.latency: float = -1.0
        self.size_score: Dict[str, float] = {}
        logging.debug("SizeMetric initialized with score=-1.0, latency=-1.0")

    def get_data(self, parsed_data: Dict[str, Any]) -> int:
        size_mb = parsed_data.get("model_size_mb", 0)
        logging.debug(f"SizeMetric.get_data extracted model_size_mb={size_mb}")
        return size_mb

    def calculate_score(self, size_mb: int) -> None:
        if size_mb <= 0:
            self.size_score = {
                d: 0.0 for d in ["raspberry_pi", "jetson_nano", "desktop_pc", "aws_server"]
            }
            self.score = 0.0
            logging.info("SizeMetric.calculate_score: size <= 0 → all device scores=0.0")
            return

        thresholds = {
            "raspberry_pi": 50,
            "jetson_nano": 200,
            "desktop_pc": 2000,
            "aws_server": 10000,
        }

        scores = {}
        for device, max_size in thresholds.items():
            if size_mb <= max_size:
                score = 0.5 + 0.5 * (1 - size_mb / max_size)
                logging.debug(
                    f"SizeMetric: {device} → within threshold {max_size} MB, raw score={score:.2f}"
                )
            else:
                score = max(0.0, 1.0 - (size_mb - max_size) / (2 * max_size))
                logging.debug(
                    f"SizeMetric: {device} → exceeds threshold {max_size} MB, raw score={score:.2f}"
                )
            scores[device] = round(max(0.0, min(score, 1.0)), 2)

        self.size_score = scores
        self.score = sum(scores.values()) / len(scores)
        logging.info(f"SizeMetric final scores={self.size_score}, overall={self.score:.2f}")

    def process_score(self, parsed_data: Dict[str, Any]) -> None:
        logging.debug("SizeMetric.process_score called")
        start_time = time.perf_counter()
        size_mb = self.get_data(parsed_data)
        self.calculate_score(size_mb)
        end_time = time.perf_counter()
        self.latency = (end_time - start_time) * 1000
        logging.debug(f"SizeMetric.process_score latency={self.latency:.2f} ms")

    def get_score(self) -> float:
        logging.debug(f"SizeMetric.get_score -> {self.score}")
        return self.score

    def get_latency(self) -> float:
        logging.debug(f"SizeMetric.get_latency -> {self.latency}")
        return self.latency

    def get_size_score(self) -> Dict[str, float]:
        logging.debug(f"SizeMetric.get_size_score -> {self.size_score}")
        return self.size_score
