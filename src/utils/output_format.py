# utils/output_format.py

import json
from typing import Dict, List, Any
from src.scorer import Scorer  # unified Scorer

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
    "security",
    "security_latency",
]


def print_score_table(rows: List[Dict[str, Any]]):
    print(json.dumps(rows, indent=4))


def format_score_row(metadata: Dict[str, Any], scorer: Scorer) -> Dict[str, Any]:
    """
    Run scorer on metadata and return a flat row dict
    matching the sample_output schema.
    """
    result = scorer.score(metadata)

    row = {
        "name": result.get("name", "Unknown"),
        "category": result.get("category", "Unknown"),
        "net_score": result.get("net_score", "N/A"),
        "net_score_latency": result.get("net_score_latency", "N/A"),
        "ramp_up_time": result.get("ramp_up_time", "N/A"),
        "ramp_up_time_latency": result.get("ramp_up_time_latency", "N/A"),
        "bus_factor": result.get("bus_factor", "N/A"),
        "bus_factor_latency": result.get("bus_factor_latency", "N/A"),
        "performance_claims": result.get("performance_claims", "N/A"),
        "performance_claims_latency": result.get("performance_claims_latency", "N/A"),
        "license": result.get("license", "N/A"),
        "license_latency": result.get("license_latency", "N/A"),
        "size_score": result.get("size_score", "N/A"),
        "size_score_latency": result.get("size_score_latency", "N/A"),
        "dataset_and_code_score": result.get("dataset_and_code_score", "N/A"),
        "dataset_and_code_score_latency": result.get("dataset_and_code_score_latency", "N/A"),
        "dataset_quality": result.get("dataset_quality", "N/A"),
        "dataset_quality_latency": result.get("dataset_quality_latency", "N/A"),
        "code_quality": result.get("code_quality", "N/A"),
        "code_quality_latency": result.get("code_quality_latency", "N/A"),
        "security": result.get("security", "N/A"),
        "security_latency": result.get("security_latency", "N/A"),
    }

    # Guarantee all columns exist
    for col in TABLE_COLUMNS:
        if col not in row:
            row[col] = "N/A"

    return row


def print_score_table_as_json(rows: List[Dict[str, Any]]):
    print(json.dumps(rows, indent=4))
