import json
import requests
from typing import List, Dict, Any

HF_MODEL_API = "https://huggingface.co/api/models/"
HF_DATASET_API = "https://huggingface.co/api/datasets/"
GH_REPO_API = "https://api.github.com/repos/"

def parse_input_file(input_url: str) -> List[Dict[str, str]]:
    """
    Parses input URL, validates it, and fetches raw metadata.
    """
    parsed_entries = []

    # Directly parse the URL passed (instead of reading from a file)
    if "huggingface.co/datasets" in input_url:
        parsed_entries.append(
            {
                "category": "DATASET",
                "url": input_url,
                "name": input_url.split("/")[-1],
            }
        )
    elif "huggingface.co" in input_url:
        parsed_entries.append(
            {
                "category": "MODEL",
                "url": input_url,
                "name": input_url.split("/")[-1],
            }
        )
    elif "github.com" in input_url:
        parsed_entries.append(
            {
                "category": "CODE",
                "url": input_url,
                "name": input_url.split("/")[-1],
            }
        )
    else:
        parsed_entries.append(
            {
                "category": "UNKNOWN",
                "url": input_url,
                "name": input_url.split("/")[-1],
            }
        )

    return parsed_entries


def fetch_metadata(entry: Dict[str, Any], debug: bool = False) -> Dict[str, Any]:
    """
    Given a parsed entry, validate the URL and fetch metadata from HuggingFace or GitHub APIs.
    Attaches a 'metadata' field to the entry.
    """
    category = entry["category"]
    url = entry["url"]

    try:
        if category == "MODEL":
            model_id = "/".join(url.split("huggingface.co/")[-1].split("/")[:2])
            resp = requests.get(HF_MODEL_API + model_id, timeout=10)
            entry["metadata"] = resp.json() if resp.status_code == 200 else {}

        elif category == "DATASET":
            dataset_id = "/".join(url.split("huggingface.co/datasets/")[-1].split("/")[:2])
            resp = requests.get(HF_DATASET_API + dataset_id, timeout=10)
            entry["metadata"] = resp.json() if resp.status_code == 200 else {}

        elif category == "CODE":
            parts = url.split("github.com/")[-1].split("/")
            if len(parts) >= 2:
                repo_path = "/".join(parts[:2])
                resp = requests.get(GH_REPO_API + repo_path, timeout=10)
                entry["metadata"] = resp.json() if resp.status_code == 200 else {}
            else:
                entry["metadata"] = {}
        else:
            entry["metadata"] = {}

    except Exception as e:
        entry["metadata"] = {"error": str(e)}

    if debug:
        print(f"\n--- RAW METADATA for {entry['name']} ({entry['category']}) ---")
        print(json.dumps(entry["metadata"], indent=2)[:2000])  # show first 2000 chars
        print("--- END ---\n")

    return entry


def demo(input_url: str, debug: bool = True):
    parsed = parse_input_file(input_url)

    for item in parsed:
        enriched = fetch_metadata(item)

        if debug:
            print(
                f"\n--{enriched.get('name', 'unknown')} ({enriched.get('category', 'UNKNOWN')}) --"
            )
            print(json.dumps(enriched.get("metadata", {}), indent=2)[:4000])
            print("--- END ---\n")

        record = {
            "name": enriched.get("name", "unknown"),
            "category": enriched.get("category", "UNKNOWN"),
            "net_score": None,
            "metrics": {},
            "links": {"url": enriched.get("url")},
            "metadata_preview": str(enriched.get("metadata", {}))[:200],
        }
        print(json.dumps(record))
