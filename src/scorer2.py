from typing import Dict, Any

from metrics.dataset_and_code import DatasetAndCodeMetric
from metrics.data_quality import DatasetQualityMetric

class Scorer:
    def __init__(self):
        self.dataset_metric = DatasetQualityMetric()
        self.code_metric = DatasetAndCodeMetric()

    def score(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        category = metadata.get("category", "").upper()

        row = {
            "name": metadata.get("name", "Unknown"),
            "category": category,
        }

        if category == "DATASET":
            self.dataset_metric.process_score(metadata)
            row["dataset_quality"] = self.dataset_metric.dataset_quality
            row["dataset_quality_latency"] = self.dataset_metric.dataset_quality_latency

        if category in ["DATASET", "CODE"]:
            self.code_metric.process_score(metadata)
            row["dataset_and_code_score"] = self.code_metric.dataset_and_code_score
            row["dataset_and_code_score_latency"] = self.code_metric.dataset_and_code_score_latency

        row.update({
            "net_score": 0.0,
            "net_score_latency": 0.0,
            "ramp_up_time": 0.0,
            "ramp_up_time_latency": 0.0,
            "bus_factor": 0.0,
            "bus_factor_latency": 0.0,
            "performance_claims": 0.0,
            "performance_claims_latency": 0.0,
            "license": 0.0,
            "license_latency": 0.0,
            "size_score": 0.0,
            "size_score_latency": 0.0,
            "code_quality": 0.0,
            "code_quality_latency": 0.0,
        })

        return row

