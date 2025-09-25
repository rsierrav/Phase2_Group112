# src/scorer.py

from typing import Dict, Any, List, Tuple
import time

# Import implemented metrics
from src.metrics.dataset_and_code import DatasetAndCodeMetric
from src.metrics.dataset_quality import DatasetQualityMetric
from src.metrics.size import SizeMetric
from src.metrics.license import LicenseMetric
from src.metrics.bus_factor import bus_factor
from src.metrics.code_quality import code_quality
from src.metrics.ramp_up_time import RampUpTime

# from src.metrics.ramp_up_time import RampUpTimeMetric
# from src.metrics.performance_claims import PerformanceClaimsMetric


class Scorer:
    """
    Runs all metrics and returns a flat dict of results.
    Handles both scalar and structured metrics (e.g., size_score dict).
    """

    def __init__(self):
        # Initialize metric objects
        dq = DatasetQualityMetric()  # LLM-based
        dac = DatasetAndCodeMetric()  # Heuristic
        sz = SizeMetric()
        lic = LicenseMetric()
        bf = bus_factor()
        cq = code_quality()
        rut = RampUpTime()
        # rtime = RampUpTimeMetric()
        # pc = PerformanceClaimsMetric()

        # Dynamic list of metrics (name, object)
        self.metrics: List[Tuple[str, Any]] = [
            # ("ramp_up_time", rtime),
            ("bus_factor", bf),
            # ("performance_claims", pc),
            ("license", lic),
            ("size_score", sz),
            ("dataset_and_code_score", dac),
            ("dataset_quality", dq),
            ("code_quality", cq),
            ("ramp_up_time", rut),
        ]

        # Define weights for each metric (should sum to ~1.0)
        self.weights: Dict[str, float] = {
            "ramp_up_time": 0.10,  # not yet implemented
            "bus_factor": 0.13,
            "performance_claims": 0.11,  # not yet implemented
            "license": 0.14,
            "size_score": 0.11,
            "dataset_and_code_score": 0.14,
            "dataset_quality": 0.14,
            "code_quality": 0.13,
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
                result[key] = {} if key == "size_score" else -1.0
                result[f"{key}_latency"] = -1.0
                print(f"[WARN] Metric {key} failed for {metadata.get('name', 'unknown')}: {e}")

        # Weighted net score calculation
        weighted_sum = 0.0
        total_weight = 0.0

        for metric, weight in self.weights.items():
            val = result.get(metric)

            if isinstance(val, (int, float)):
                if val >= 0:  # ignore -1 placeholders
                    weighted_sum += val * weight
                    total_weight += weight
            elif isinstance(val, dict):  # e.g., size_score
                if val:
                    avg_size = sum(val.values()) / len(val)
                    weighted_sum += avg_size * weight
                    total_weight += weight

        result["net_score"] = weighted_sum / total_weight if total_weight > 0 else -1.0

        # Net score latency = total elapsed time (ms)
        end_time = time.perf_counter()
        result["net_score_latency"] = (end_time - start_time) * 1000

        return result
