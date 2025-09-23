# scorer.py
from typing import List, Dict, Any
import time
from src.metrics.performance_claims import PerformanceClaimsMetric
from src.metrics.license import LicenseMetric

# Placeholder imports for other metrics (not implemented yet)
# from src.metrics.bus_factor import BusFactorMetric
# from src.metrics.ramp_up_time import RampUpTimeMetric
# from src.metrics.size_score import SizeScoreMetric
# from src.metrics.dataset_and_code import DatasetAndCodeMetric
# from src.metrics.dataset_quality import DatasetQualityMetric
# from src.metrics.code_quality import CodeQualityMetric


def score(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score a single parsed entry using all metrics.
    Returns a dict with flattened per-metric scores + latencies
    and net_score/net_score_latency.
    """
    result: Dict[str, Any] = {
        "name": entry.get("name", "unknown"),
        "category": entry.get("category", "UNKNOWN"),
    }

    # List of metric objects and their output key names
    metrics: List = [
        #("performance_claims", PerformanceClaimsMetric()),
        #("license", LicenseMetric()),
        # ("bus_factor", BusFactorMetric()),  # TODO: implement
        # ("ramp_up_time", RampUpTimeMetric()),  # TODO: implement
        # ("size_score", SizeScoreMetric()),  # TODO: implement
        # ("dataset_and_code_score", DatasetAndCodeMetric()),  # TODO: implement
        # ("dataset_quality", DatasetQualityMetric()),  # TODO: implement
        # ("code_quality", CodeQualityMetric()),  # TODO: implement
    ]

    start_time = time.perf_counter()

    for key, metric in metrics:
        try:
            metric.process_score(entry)
            result[key] = metric.get_score()
            result[f"{key}_latency"] = metric.get_latency()
        except Exception as e:
            result[key] = 0.0
            result[f"{key}_latency"] = 0.0
            print(f"[WARN] Metric {key} failed for {entry.get('name')}: {e}")

    # Compute net score as average of scalar metrics
    scalar_scores = [
        v for k, v in result.items()
        if not k.endswith("_latency") and isinstance(v, (int, float))
    ]
    result["net_score"] = sum(scalar_scores) / len(scalar_scores) if scalar_scores else 0.0

    # Net score latency = total time to compute all metrics
    end_time = time.perf_counter()
    result["net_score_latency"] = (end_time - start_time) * 1000  # milliseconds

    return result
