from typing import Any, Dict
import time
import logging
from .protocol import Metric


class PerformanceClaims(Metric):
    """Evaluate evidence of performance claims for a given model."""

    def __init__(self) -> None:
        self.score: float = 0.0
        self.latency: float = 0.0

    def get_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        metadata = parsed_data.get("metadata", {})
        data = {
            "model_index": metadata.get("model-index", []),
            "tags": metadata.get("tags", []),
            "cardData": metadata.get("cardData", {}),
            "downloads": metadata.get("downloads", 0),
            "likes": metadata.get("likes", 0),
            "category": parsed_data.get("category", "UNKNOWN"),
        }
        logging.debug(f"PerformanceClaims.get_data keys={list(data.keys())}")
        return data

    def calculate_score(self, data: Dict[str, Any]) -> None:
        category = data.get("category", "UNKNOWN")
        if category != "MODEL":
            self.score = 0.0
            logging.info("Not a MODEL entry -> score=0.0")
            return

        score = 0.0

        model_index = data.get("model_index", [])
        if model_index and isinstance(model_index, list):
            for model_entry in model_index:
                if isinstance(model_entry, dict) and model_entry.get("results"):
                    score += 0.5
                    if len(model_entry["results"]) > 1:
                        score += 0.2
                    break

        tags = data.get("tags", [])
        perf_tags = [
            "arxiv:",
            "leaderboard",
            "benchmark",
            "evaluation",
            "sota",
            "state-of-the-art",
            "performance",
        ]
        if any(any(pt in tag.lower() for pt in perf_tags) for tag in tags if isinstance(tag, str)):
            score += 0.25

        card_data = data.get("cardData", {})
        if isinstance(card_data, dict) and card_data.get("model-index", []) and not model_index:
            score += 0.3

        downloads = data.get("downloads", 0)
        likes = data.get("likes", 0)
        if downloads > 100000 or likes > 500:
            score += 0.4
        elif downloads > 10000 or likes > 100:
            score += 0.3
        elif downloads > 1000 or likes > 10:
            score += 0.2
        elif downloads > 100 or likes > 5:
            score += 0.1

        if score == 0.0:
            score = 0.1

        self.score = min(score, 1.0)
        logging.info(
            f"PerformanceClaims score={self.score:.2f} (downloads={downloads}, likes={likes})"
        )

    def process_score(self, parsed_data: Dict[str, Any]) -> None:
        start_time = time.perf_counter()
        try:
            data = self.get_data(parsed_data)
            self.calculate_score(data)
        except Exception as e:
            self.score = 0.0
            logging.error(f"Error in PerformanceClaims: {e}", exc_info=True)
        end_time = time.perf_counter()
        self.latency = (end_time - start_time) * 1000
        logging.debug(f"PerformanceClaims latency={self.latency:.2f} ms")

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> float:
        return self.latency
