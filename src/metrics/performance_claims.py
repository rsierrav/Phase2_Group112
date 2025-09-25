# performance_claims.py
from typing import Any, Dict
import time
from .protocol import Metric


class PerformanceClaims(Metric):
    """
    Metric to evaluate the evidence of good performance for a given model,
    dataset, or code URL.
    Scores are normalized between 0 and 1:
      - 0: no evidence
      - 0.5: partial or weak evidence
      - 1: strong evidence
    """

    def __init__(self) -> None:
        self.score: float = 0.0
        self.latency: float = 0.0  # in milliseconds

    def get_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant metadata from the parsed entry.
        Returns a dict with information that will be used to calculate score.
        """
        metadata = parsed_data.get("metadata", {})
        category = parsed_data.get("category", "UNKNOWN")

        if category == "MODEL":
            metrics = metadata.get("metrics", [])
            paperswithcode = metadata.get("paperswithcode", {})
            benchmark_results = metadata.get("benchmark_results", [])
            return {
                "metrics": metrics,
                "paperswithcode": paperswithcode,
                "benchmark_results": benchmark_results,
                "category": category
            }

        elif category == "DATASET":
            dataset_stats = metadata.get("dataset_stats", {})
            citations = metadata.get("citations", 0)
            benchmark_results = metadata.get("benchmark_results", [])
            return {
                "dataset_stats": dataset_stats,
                "citations": citations,
                "benchmark_results": benchmark_results,
                "category": category
            }

        elif category == "CODE":
            test_results = metadata.get("test_results", {})
            example_results = metadata.get("example_results", [])
            return {
                "test_results": test_results,
                "example_results": example_results,
                "category": category
            }

        # fallback for unknown category
        return {"category": category}

    def calculate_score(self, data: Dict[str, Any]) -> None:
        """
        Compute the performance claims score using a heuristic:
        - MODEL: metrics + paperswithcode + benchmark results
        - DATASET: dataset stats + citations + benchmark results
        - CODE: test coverage + example results
        Returns score between 0 and 1.
        """
        category = data.get("category", "UNKNOWN")

        if category == "MODEL":
            score = 0.0
            if data.get("metrics"):
                score += 0.4
            if data.get("paperswithcode"):
                score += 0.4
            if data.get("benchmark_results"):
                score += 0.2
            self.score = min(score, 1.0)

        elif category == "DATASET":
            score = 0.0
            if data.get("dataset_stats"):
                score += 0.3
            if data.get(
                "citations", 0
            ) > 5:  # arbitrary threshold for "well-cited"
                score += 0.3
            if data.get("benchmark_results"):
                score += 0.4
            self.score = min(score, 1.0)

        elif category == "CODE":
            score = 0.0
            test_results = data.get("test_results", {})
            if test_results.get("coverage", 0) >= 50:  # threshold 50%
                score += 0.5
            if data.get("example_results"):
                score += 0.5
            self.score = min(score, 1.0)

        else:
            # Unknown category gets minimal score
            self.score = 0.0

    def process_score(self, parsed_data: Dict[str, Any]) -> None:
        """
        Main processing function:
        - Extract data
        - Calculate score
        - Record latency in milliseconds
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
        """Return the current performance claims score."""
        return self.score

    def get_latency(self) -> float:
        """Return the time taken to compute score in milliseconds."""
        return self.latency
