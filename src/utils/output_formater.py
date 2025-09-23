# src/output_formatter.py

import json
from typing import Dict, Any, Optional


class OutputFormatter:
    """
    Collects metric results and outputs them in NDJSON format.
    Allows flexible adding/removing of metrics.
    """

    def __init__(self, base_entry: Optional[Dict[str, Any]] = None):
        # Fallback to empty dict if no entry provided
        self.base_entry: Dict[str, Any] = base_entry or {}
        self.metrics: Dict[str, Any] = {}

    def add_metric_score(
        self, name: str, metric_obj: Any, extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a metric's score + latency to the formatter.
        If the metric has additional structured results (e.g., size_score dict),
        you can pass them via `extra`.
        """
        self.metrics[name] = metric_obj.get_score()
        self.metrics[f"{name}_latency"] = round(metric_obj.get_latency())

        # Merge in optional extra info (e.g., nested dicts)
        if extra:
            for k, v in extra.items():
                self.metrics[k] = v

    def build_output(self, net_score: Optional[float] = None) -> Dict[str, Any]:
        """
        Build a dictionary ready to be dumped as NDJSON.
        """
        output = {
            "name": self.base_entry.get("name", "unknown"),
            "category": self.base_entry.get("category", "UNKNOWN"),
            "net_score": net_score,  # caller can pass computed net_score
            "metrics": self.metrics,
            "links": {"url": self.base_entry.get("url", "")},
            "metadata_preview": str(self.base_entry.get("metadata", {}))[:200],
        }
        return output

    def print_scores(self, net_score: Optional[float] = None) -> None:
        """
        Print the output in NDJSON format (1 line per entry).
        """
        output = self.build_output(net_score)
        print(json.dumps(output))
