from typing import Any, Dict
from .protocol import Metric


class example_metric(Metric):
    def __init__(self):
        self.score: float = 0.0

    def get_data(self, parsed_data: Dict[str, Any]) -> str:
        return parsed_data.get("license", "")

    def calculate_score(self, data: Any) -> None:
        if data in {"MIT", "Apache-2.0"}:
            self.score = 1.0
        else:
            self.score = 0.0

    def get_score(self) -> float:
        return self.score
