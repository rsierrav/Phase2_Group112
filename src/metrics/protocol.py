# src/metrics/protocol.py

from typing import Protocol, Any, Dict
import time


class Metric(Protocol):
    """
    Protocol for all metrics.
    Every metric must follow this structure so the system
    can automatically run and fetch results.
    """

    # Each metric keeps an internal score
    score: float
    latency: float  # in milliseconds

    def get_data(self, parsed_data: Dict[str, Any]) -> Any:
        """
        Extract and preprocess the data this metric needs
        from the parser output (e.g., repo info, model card).
        Returns a data structure used by calculate_score().
        """
        ...

    def calculate_score(self, data: Any) -> None:
        """
        Compute the metric score based on extracted data.
        Updates the internal `score`.
        """
        ...

    def process_score(self, parsed_data: Dict[str, Any]) -> None:
        """
        Process the metric: measure latency and compute score.
        Updates `score` and `latency` attributes.
        """
        start_time = time.perf_counter()  # high-resolution timer
        data = self.get_data(parsed_data)
        self.calculate_score(data)
        end_time = time.perf_counter()

        # store latency in milliseconds
        self.latency = (end_time - start_time) * 1000

    def get_score(self) -> float:
        """
        Return the current score (calculated by calculate_score()).
        """
        return getattr(self, "score", 0.0)

    def get_latency(self) -> float:
        """
        Return the time taken to compute the score in milliseconds.
        """
        return getattr(self, "latency", 0.0)

