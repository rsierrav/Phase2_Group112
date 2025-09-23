import json
from typing import Dict, List, Any
from scorer2 import Scorer

TABLE_COLUMNS = [
    "name",
    "category",
    "net_score",
    "net_score_latency",
    "ramp_up_time",
    "ramp_up_time_latency",
    "bus_factor",
    "bus_factor_latency",
    "performance_claims",
    "performance_claims_latency",
    "license",
    "license_latency",
    "size_score",
    "size_score_latency",
    "dataset_and_code_score",
    "dataset_and_code_score_latency",
    "dataset_quality",
    "dataset_quality_latency",
    "code_quality",
    "code_quality_latency",
]


def print_score_table(rows: List[Dict[str, Any]]):
    print(json.dumps(rows, indent=4))


def format_score_row(metadata: Dict[str, Any], scorer: Scorer) -> Dict[str, Any]:
    scorer.score(metadata)

    # "name": metadata.get("name", "Unknown"),
    # "category": metadata.get("category", "Unknown"),
    row = {
        "dataset_and_code_score": getattr(scorer.code_metric, "dataset_and_code_score", ""),
        "dataset_and_code_score_latency": getattr(
            scorer.code_metric, "dataset_and_code_score_latency", "N/A"
        ),
        "dataset_quality": getattr(scorer.dataset_metric, "dataset_quality", "N/A"),
        "dataset_quality_latency": getattr(scorer.dataset_metric, "dataset_quality_latency", "N/A"),
    }

    for col in TABLE_COLUMNS:
        if col not in row:
            row[col] = "N/A"

    return row


def print_score_table_as_json(rows: List[Dict[str, Any]]):
    print(json.dumps(rows, indent=4))
