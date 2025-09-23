import json
import requests
from typing import List, Dict, Any

"""
Parses input URLs, validates them, and fetches raw metadata.
This file does not calculate metrics — it just collects data
"""

HF_MODEL_API = "https://huggingface.co/api/models/"
HF_DATASET_API = "https://huggingface.co/api/datasets/"
GH_REPO_API = "https://api.github.com/repos/"


def parse_input_file(input_path: str) -> List[Dict[str, str]]:
    parsed_entries = []

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            urls = [u.strip() for u in line.split(",") if u.strip()]
            if not urls:
                continue

            for url in urls:
                if "huggingface.co/datasets" in url:
                    parsed_entries.append(
                        {
                            "category": "DATASET",
                            "url": url,
                            "name": url.split("/")[-1],
                        }
                    )
                elif "huggingface.co" in url:
                    parsed_entries.append(
                        {
                            "category": "MODEL",
                            "url": url,
                            "name": url.split("/")[-1],
                        }
                    )
                elif "github.com" in url:
                    parsed_entries.append(
                        {
                            "category": "CODE",
                            "url": url,
                            "name": url.split("/")[-1],
                        }
                    )
                else:
                    parsed_entries.append(
                        {
                            "category": "UNKNOWN",
                            "url": url,
                            "name": url.split("/")[-1],
                        }
                    )

    return parsed_entries


def fetch_metadata(entry: Dict[str, Any], debug: bool = False) -> Dict[str, Any]:
    """
    Given a parsed entry, validate the URL and fetch metadata
    from HuggingFace or GitHub APIs.
    Attaches a 'metadata' field to the entry.
    Adds 'model_size_mb' for MODEL entries if available.
    If debug=True, prints the raw JSON.
    """
    category = entry["category"]
    url = entry["url"]

    try:
        if category == "MODEL":
            model_id = "/".join(url.split("huggingface.co/")[-1].split("/")[:2])
            resp = requests.get(HF_MODEL_API + model_id, timeout=10)
            entry["metadata"] = resp.json() if resp.status_code == 200 else {}

            # --- Extract model size ---
            size_bytes = 0
            md = entry["metadata"]

            # usedStorage field
            if "usedStorage" in md and isinstance(md["usedStorage"], (int, float)):
                size_bytes = md["usedStorage"]

            # sum sizes of files in siblings
            elif "siblings" in md and isinstance(md["siblings"], list):
                for s in md:
                    if isinstance(s, dict) and "size" in s:
                        size_bytes += s["size"]

            entry["model_size_mb"] = round(size_bytes / (1024 * 1024), 2) if size_bytes else 0.0

        elif category == "DATASET":
            dataset_id = "/".join(url.split("huggingface.co/datasets/")[-1].split("/")[:2])
            resp = requests.get(HF_DATASET_API + dataset_id, timeout=10)
            entry["metadata"] = resp.json() if resp.status_code == 200 else {}

            # Note: no dataset size available
            entry["dataset_size_mb"] = None

        elif category == "CODE":
            parts = url.split("github.com/")[-1].split("/")
            if len(parts) >= 2:
                repo_path = "/".join(parts[:2])
                resp = requests.get(GH_REPO_API + repo_path, timeout=10)
                entry["metadata"] = resp.json() if resp.status_code == 200 else {}
            else:
                entry["metadata"] = {}

            if "size" in entry["metadata"]:
                entry["repo_size_kb"] = entry["metadata"]["size"]
            else:
                entry["repo_size_kb"] = None

        else:
            entry["metadata"] = {}

    except Exception as e:
        entry["metadata"] = {"error": str(e)}

    if debug:
        print(f"\n RAW METADATA for {entry['name']} ({entry['category']})")
        print(json.dumps(entry["metadata"], indent=2)[:2000])
        print("END \n")

    return entry


def demo(input_file: str, debug: bool = True):
    parsed = parse_input_file(input_file)

    for item in parsed:
        enriched = fetch_metadata(item)

        # If debug mode, show full metadata for inspection
        if debug:
            print(f"\n{enriched.get('name', 'unknown')} ({enriched.get('category', 'UNKNOWN')})")
            print(json.dumps(enriched.get("metadata", {}), indent=2)[:4000])
            print("END\n")

        record = {
            "name": enriched.get("name", "unknown"),
            "category": enriched.get("category", "UNKNOWN"),
            "net_score": None,
            "metrics": {},
            "links": {"url": enriched.get("url")},
            "metadata_preview": str(enriched.get("metadata", {}))[:200],
        }
        print(json.dumps(record))
