# utils/output_format.py

import json
import logging
from typing import Dict, List, Any
from src.scorer import Scorer

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
    logging.debug(f"Printing score table for {len(rows)} rows")
    print(json.dumps(rows, indent=4))


def format_score_row(metadata: Dict[str, Any], scorer: Scorer) -> Dict[str, Any]:
    """
    Run scorer on metadata and return a flat row dict
    matching the sample_output schema.
    """
    logging.debug(f"Formatting score row for: {metadata.get('name', 'unknown')}")
    result = scorer.score(metadata)

    def as_float(val, default=0.0, is_latency=False):
        try:
            if is_latency:
                return round(float(val))
            else:
                return round(float(val), 2)
        except (TypeError, ValueError):
            logging.warning(f"Failed to coerce value {val} to float, using default={default}")
            return default

    row = {
        "name": result.get("name", "unknown"),
        "category": result.get("category", "unknown"),
        "net_score": as_float(result.get("net_score"), -1),
        "net_score_latency": as_float(result.get("net_score_latency"), -1, is_latency=True),
        "ramp_up_time": as_float(result.get("ramp_up_time"), -1),
        "ramp_up_time_latency": as_float(result.get("ramp_up_time_latency"), -1, is_latency=True),
        "bus_factor": as_float(result.get("bus_factor"), -1),
        "bus_factor_latency": as_float(result.get("bus_factor_latency"), -1, is_latency=True),
        "performance_claims": as_float(result.get("performance_claims"), -1),
        "performance_claims_latency": as_float(
            result.get("performance_claims_latency"), -1, is_latency=True
        ),
        "license": as_float(result.get("license"), -1),
        "license_latency": as_float(result.get("license_latency"), -1, is_latency=True),
        "size_score": {
            "raspberry_pi": as_float(result.get("size_score", {}).get("raspberry_pi"), -1),
            "jetson_nano": as_float(result.get("size_score", {}).get("jetson_nano"), -1),
            "desktop_pc": as_float(result.get("size_score", {}).get("desktop_pc"), -1),
            "aws_server": as_float(result.get("size_score", {}).get("aws_server"), -1),
        },
        "size_score_latency": as_float(result.get("size_score_latency"), -1, is_latency=True),
        "dataset_and_code_score": as_float(result.get("dataset_and_code_score"), -1),
        "dataset_and_code_score_latency": as_float(
            result.get("dataset_and_code_score_latency"), -1, is_latency=True
        ),
        "dataset_quality": as_float(result.get("dataset_quality"), -1),
        "dataset_quality_latency": as_float(
            result.get("dataset_quality_latency"), -1, is_latency=True
        ),
        "code_quality": as_float(result.get("code_quality"), -1),
        "code_quality_latency": as_float(result.get("code_quality_latency"), -1, is_latency=True),
    }

    for col in TABLE_COLUMNS:
        if col not in row:
            logging.debug(f"Adding missing column {col} with default value 0.0")
            row[col] = 0.0

    logging.info(f"Formatted score row for {row['name']}, net_score={row['net_score']}")
    return row


def print_score_table_as_json(rows: List[Dict[str, Any]]):
    logging.debug(f"Printing score table as JSON with {len(rows)} rows")
    print(json.dumps(rows, indent=4))
