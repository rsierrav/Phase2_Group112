# src/scorer.py

from typing import Dict, Any, List, Tuple, Union
import time
import concurrent.futures
import multiprocessing
import copy
import logging

# Import implemented metrics
from src.metrics.dataset_and_code import DatasetAndCodeMetric
from src.metrics.dataset_quality import DatasetQualityMetric
from src.metrics.size import SizeMetric
from src.metrics.license import LicenseMetric
from src.metrics.bus_factor import bus_factor
from src.metrics.code_quality import code_quality
from src.metrics.ramp_up_time import RampUpTime
from src.metrics.performance_claims import PerformanceClaims


def run_metric(metric_info: Tuple[str, Any], metadata: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Helper function to run a single metric in a separate process/thread.
    Returns the metric name and its results.
    """
    key, metric = metric_info
    logging.debug(f"Running metric: {key}")

    try:
        metadata_copy = copy.deepcopy(metadata)
        metric.process_score(metadata_copy)

        if key == "size_score" and hasattr(metric, "get_size_score"):
            score = metric.get_size_score()
        else:
            score = metric.get_score()

        latency = metric.get_latency()
        logging.debug(f"Metric {key} completed with score={score}, latency={latency:.2f} ms")

        return key, {"score": score, "latency": latency, "success": True}

    except Exception as e:
        logging.error(f"Metric {key} failed: {e}", exc_info=True)
        return key, {
            "score": {} if key == "size_score" else -1.0,
            "latency": -1.0,
            "success": False,
            "error": str(e),
        }


class Scorer:
    """
    Runs all metrics in parallel and returns a flat dict of results.
    Handles both scalar and structured metrics (e.g., size_score dict).
    """

    def __init__(self):
        logging.debug("Initializing Scorer with all metrics")
        dq = DatasetQualityMetric()
        dac = DatasetAndCodeMetric()
        sz = SizeMetric()
        lic = LicenseMetric()
        bf = bus_factor()
        cq = code_quality()
        rut = RampUpTime()
        pc = PerformanceClaims()

        self.metrics: List[Tuple[str, Any]] = [
            ("bus_factor", bf),
            ("performance_claims", pc),
            ("license", lic),
            ("size_score", sz),
            ("dataset_and_code_score", dac),
            ("dataset_quality", dq),
            ("code_quality", cq),
            ("ramp_up_time", rut),
        ]

        self.weights: Dict[str, float] = {
            "ramp_up_time": 0.10,
            "bus_factor": 0.13,
            "performance_claims": 0.11,
            "license": 0.14,
            "size_score": 0.11,
            "dataset_and_code_score": 0.14,
            "dataset_quality": 0.14,
            "code_quality": 0.13,
        }

    def score(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        logging.info(f"Scoring metadata for {metadata.get('name', 'Unknown')}")
        result: Dict[str, Union[float, Dict[str, float], str]] = {
            "name": metadata.get("name", "Unknown"),
            "category": metadata.get("category", "UNKNOWN"),
        }

        start_time = time.perf_counter()
        max_workers = min(multiprocessing.cpu_count(), len(self.metrics))
        logging.debug(f"Using {max_workers} workers for scoring")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_metric = {executor.submit(run_metric, metric_info, metadata): metric_info[0] for metric_info in self.metrics}
            for future in concurrent.futures.as_completed(future_to_metric):
                metric_name = future_to_metric[future]
                try:
                    key, metric_result = future.result()
                    if not metric_result["success"]:
                        logging.warning(f"Metric {key} failed: {metric_result.get('error', 'Unknown error')}")
                    result[key] = metric_result["score"]
                    result[f"{key}_latency"] = metric_result["latency"]
                except Exception as e:
                    logging.error(f"Metric {metric_name} crashed: {e}", exc_info=True)
                    result[metric_name] = {} if metric_name == "size_score" else -1.0
                    result[f"{metric_name}_latency"] = -1.0

        weighted_sum = 0.0
        total_weight = 0.0
        for metric, weight in self.weights.items():
            val = result.get(metric)
            if isinstance(val, (int, float)):
                if val >= 0:
                    weighted_sum += val * weight
                    total_weight += weight
            elif isinstance(val, dict):
                if val:
                    avg_size = sum(val.values()) / len(val)
                    weighted_sum += avg_size * weight
                    total_weight += weight

        result["net_score"] = weighted_sum / total_weight if total_weight > 0 else -1.0
        end_time = time.perf_counter()
        result["net_score_latency"] = (end_time - start_time) * 1000
        logging.info(
            f"Finished scoring {metadata.get('name', 'Unknown')}, net_score={result['net_score']:.2f}, latency={result['net_score_latency']:.2f} ms"
        )

        return result
