from typing import Protocol, Any, Dict


class Metric(Protocol):
    """
    Protocol for all metrics.
    Every metric must follow this structure so the system
    can automatically run and fetch results.
    """

    # Each metric keeps an internal score
    score: float

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

    def get_score(self) -> float:
        """
        Return the current score (calculated by calculate_score()).
        """
        ...
