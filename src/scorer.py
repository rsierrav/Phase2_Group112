# src/scorer.py

from typing import Dict, Any, List, Tuple
import time

# Import all metrics
from metrics.data_quality import DatasetQualityMetric
from metrics.dataset_and_code import DatasetAndCodeMetric
from metrics.dataset_quality import DatasetCodeMetric
from metrics.size import SizeMetric
from metrics.license import LicenseMetric
from metrics.bus_factor import bus_factor
from metrics.code_quality import code_quality
from metrics.security import SecurityMetric


class Scorer:
    """
    runs all metrics and returns a flat dict of results.
    Handles both scalar and structured metrics (e.g., size_score dict).
    """

    def __init__(self):
        # Initialize metric objects
        dq = DatasetQualityMetric()
        dac = DatasetAndCodeMetric()
        dcode = DatasetCodeMetric()
        sz = SizeMetric()
        lic = LicenseMetric()
        bf = bus_factor()
        cq = code_quality()
        sq = SecurityMetric()

        # Dynamic list of metrics (name, object)
        self.metrics: List[Tuple[str, Any]] = [
            ("dataset_quality", dq),
            ("dataset_and_code_score", dac),
            ("dataset_code", dcode),
            ("size_score", sz),
            ("license", lic),
            ("bus_factor", bf),
            ("code_quality", cq),
            ("security", sq),
        ]

        # Define weights for each metric (must sum ~1.0)
        self.weights: Dict[str, float] = {
            "ramp_up_time": 0.08,  # not yet implemented
            "bus_factor": 0.12,
            "performance_claims": 0.10,  # not yet implemented
            "license": 0.12,
            "size_score": 0.10,
            "dataset_and_code_score": 0.12,
            "dataset_quality": 0.12,
            "code_quality": 0.09,
            "security": 0.15,
        }

    def score(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all metrics on metadata and return a flat dict with scores + latencies.
        """

        result: Dict[str, Any] = {
            "name": metadata.get("name", "Unknown"),
            "category": metadata.get("category", "UNKNOWN"),
        }

        start_time = time.perf_counter()

        # Run each metric and collect results
        for key, metric in self.metrics:
            try:
                metric.process_score(metadata)

                # Special case: size_score may return a dict
                if key == "size_score" and hasattr(metric, "get_size_score"):
                    result[key] = metric.get_size_score()
                else:
                    result[key] = metric.get_score()

                result[f"{key}_latency"] = metric.get_latency()

            except Exception as e:
                result[key] = {} if key == "size_score" else 0.0
                result[f"{key}_latency"] = 0.0
                print(f"[WARN] Metric {key} failed for {metadata.get('name', 'unknown')}: {e}")

        # Weighted net score calculation
        weighted_sum = 0.0
        total_weight = 0.0

        for metric, weight in self.weights.items():
            val = result.get(metric)

            if isinstance(val, (int, float)):
                weighted_sum += val * weight
                total_weight += weight
            elif isinstance(val, dict):  # e.g., size_score
                if val:
                    avg_size = sum(val.values()) / len(val)
                    weighted_sum += avg_size * weight
                    total_weight += weight

        result["net_score"] = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Net score latency = total elapsed time
        end_time = time.perf_counter()
        result["net_score_latency"] = (end_time - start_time) * 1000  # ms

        return result
