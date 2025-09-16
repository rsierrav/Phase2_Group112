import json
from typing import List, Dict

"""
Reads an input file containing comma-separated URLs and parses them
into structured dictionaries with category inference.
"""


def parse_input_file(input_path: str) -> List[Dict[str, str]]:

    parsed_entries = []

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            urls = [u.strip() for u in line.split(",") if u.strip()]
            if not urls:
                continue

            entry = {}
            for url in urls:
                if "huggingface.co/datasets" in url:
                    entry["dataset"] = url
                elif "huggingface.co" in url or "github.com" in url:
                    # Could refine later with HuggingFace model API
                    entry["model"] = url
                else:
                    entry["code"] = url
            parsed_entries.append(entry)

    return parsed_entries


"""
Demo: Parse the input file and print NDJSON-like records
(stub metrics for now).
"""


def demo(input_file: str):
    parsed = parse_input_file(input_file)

    for item in parsed:
        # Stub data – metrics team will replace these placeholders
        record = {
            "name": item.get("model", "unknown").split("/")[-1],
            "category": "MODEL" if "model" in item else "DATASET",
            "net_score": None,  # placeholder
            "metrics": {
                "license": None,
                "size": None,
                "bus_factor": None,
                "ramp_up_time": None,
                "dataset_quality": None,
                "code_quality": None,
                "performance_claims": None,
            },
            "links": item,
        }
        print(json.dumps(record))  # NDJSON line
