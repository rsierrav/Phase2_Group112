from typing import Any, Dict
import time
from .protocol import Metric


class PerformanceClaims(Metric):
    """
    Metric to evaluate the evidence of good performance for a given model.
    Analyzes model-index, benchmark results, and performance metrics.
    """

    def __init__(self) -> None:
        self.score: float = 0.0
        self.latency: float = 0.0

    def get_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract performance-related data from HuggingFace metadata.
        """
        metadata = parsed_data.get("metadata", {})

        return {
            "model_index": metadata.get("model-index", []),
            "tags": metadata.get("tags", []),
            "cardData": metadata.get("cardData", {}),
            "downloads": metadata.get("downloads", 0),
            "likes": metadata.get("likes", 0),
            "category": parsed_data.get("category", "UNKNOWN"),
        }

    def calculate_score(self, data: Dict[str, Any]) -> None:
        """
        Calculate performance claims score based on available evidence.
        """
        category = data.get("category", "UNKNOWN")

        if category != "MODEL":
            self.score = 0.0
            return

        score = 0.0

        # Check for model-index with benchmark results
        model_index = data.get("model_index", [])
        if model_index and isinstance(model_index, list):
            for model_entry in model_index:
                if isinstance(model_entry, dict):
                    results = model_entry.get("results", [])
                    if results:
                        score += 0.4

                        # Bonus for multiple benchmarks
                        if len(results) > 1:
                            score += 0.1
                        break

        # Check for performance-related tags
        tags = data.get("tags", [])
        performance_tags = [
            "arxiv:",
            "leaderboard",
            "benchmark",
            "evaluation",
            "sota",
            "state-of-the-art",
            "performance",
        ]

        has_performance_tags = any(any(perf_tag in tag.lower() for perf_tag in performance_tags) for tag in tags if isinstance(tag, str))

        if has_performance_tags:
            score += 0.2

        # Check cardData for additional performance info
        card_data = data.get("cardData", {})
        if isinstance(card_data, dict):
            # Look for model-index in cardData too
            card_model_index = card_data.get("model-index", [])
            if card_model_index and not model_index:  # Avoid double counting
                score += 0.3

        # Community validation (downloads/likes as weak evidence)
        downloads = data.get("downloads", 0)
        likes = data.get("likes", 0)

        if downloads > 1000 or likes > 10:
            score += 0.1
        elif downloads > 100 or likes > 5:
            score += 0.05

        if downloads > 10000:  # extremely widely used model
            score = max(score, 0.5)
        elif downloads > 1000:
            score = max(score, 0.3)

        # Cap the score at 1.0
        self.score = min(score, 1.0)

    def process_score(self, parsed_data: Dict[str, Any]) -> None:
        """
        Main processing function with timing.
        """
        start_time = time.perf_counter()
        try:
            data = self.get_data(parsed_data)
            self.calculate_score(data)
        except Exception as e:
            self.score = 0.0
            print(f"[PerformanceClaims] Error calculating score: {e}")
        end_time = time.perf_counter()
        self.latency = (end_time - start_time) * 1000

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> float:
        return self.latency
