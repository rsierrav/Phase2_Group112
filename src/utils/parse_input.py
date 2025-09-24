import json
import requests
import os
from typing import List, Dict, Any

"""
Parses input URLs, validates them, and fetches raw metadata (models only).
This file does not calculate metrics — it just collects data.
"""

HF_MODEL_API = "https://huggingface.co/api/models/"
GH_REPO_API = "https://api.github.com/repos/"


def parse_input_file(input_path: str) -> List[Dict[str, str]]:
    """
    Parses input file containing URLs (comma-separated or line-by-line).

    Args:
        input_path: File path containing URLs

    Returns:
        List of dictionaries with category, url, and name fields
    """
    parsed_entries: List[Dict[str, str]] = []

    if not input_path or not input_path.strip():
        print("Warning: Empty or None input provided")
        return []

    input_path = input_path.strip()

    # Check if input_path is a file that exists
    if os.path.isfile(input_path):
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                print(f"Warning: No content found in file {input_path}")
                return []

            all_urls: List[str] = []
            for line in content.split("\n"):
                if not line.strip():
                    continue
                urls_in_line = [
                    url.strip().strip('"').strip("'") for url in line.split(",")
                ]
                for url in urls_in_line:
                    if url:
                        all_urls.append(url)
        except Exception as e:
            print(f"Error reading file {input_path}: {e}")
            return []
    else:
        all_urls = [input_path]

    for url in all_urls:
        entry = categorize_url(url)
        if entry:
            parsed_entries.append(entry)
        else:
            print(f"Warning: Could not categorize URL: {url}")

    return parsed_entries


def categorize_url(url: str) -> Dict[str, str] | None:
    """
    Categorizes a single URL and returns structured entry.
    """
    if not url or not isinstance(url, str):
        return None

    url = url.strip()
    if not url or "." not in url:
        return None

    try:
        if "huggingface.co/datasets" in url:
            # DATASET
            parts = url.split("/")
            name = parts[-1] if parts[-1] else parts[-2]
            return {"category": "DATASET", "url": url, "name": name}

        elif "huggingface.co" in url:
            # MODEL (ignore /spaces/ and profiles)
            parts = url.split("/")
            if "spaces" in parts:
                return {"category": "UNKNOWN", "url": url, "name": "unknown"}
            name = parts[-1] if parts[-1] else parts[-2]
            return {"category": "MODEL", "url": url, "name": name}

        elif "github.com" in url:
            # CODE (use repo name, not org)
            parts = url.split("github.com/")[-1].split("/")
            if len(parts) >= 2:
                repo_name = parts[1]
                return {"category": "CODE", "url": url, "name": repo_name}
            return {"category": "CODE", "url": url, "name": "unknown"}

        else:
            return {"category": "UNKNOWN", "url": url, "name": "unknown"}
    except Exception:
        return None


def fetch_metadata(entry: Dict[str, Any], debug: bool = False) -> Dict[str, Any]:
    """
    Fetches metadata only for MODEL entries from Hugging Face.
    Attaches 'metadata' field and 'model_size_mb' if available.
    Other categories are returned unchanged.
    """
    category = entry.get("category", "UNKNOWN")
    url = entry.get("url", "")
    entry["metadata"] = {}

    if category != "MODEL":
        # Skip metadata fetch for non-model entries
        return entry

    try:
        model_id = "/".join(url.split("huggingface.co/")[-1].split("/")[:2])
        if not model_id or model_id == "/":
            raise ValueError("Could not extract model ID")

        resp = requests.get(HF_MODEL_API + model_id, timeout=10)
        if resp.status_code == 200:
            entry["metadata"] = resp.json()
        else:
            entry["metadata"] = {"error": f"HTTP {resp.status_code}: {resp.reason}"}

        # Try to compute size
        md = entry["metadata"]
        size_bytes = 0
        if isinstance(md, dict) and "error" not in md:
            if "usedStorage" in md and isinstance(md["usedStorage"], (int, float)):
                size_bytes = md["usedStorage"]
            elif "siblings" in md and isinstance(md["siblings"], list):
                for s in md["siblings"]:
                    if isinstance(s, dict) and isinstance(s.get("size"), (int, float)):
                        size_bytes += s["size"]
        entry["model_size_mb"] = (
            round(size_bytes / (1024 * 1024), 2) if size_bytes > 0 else 0.0
        )

    except Exception as e:
        entry["metadata"] = {"error": f"Unexpected error: {str(e)}"}
        entry["model_size_mb"] = 0.0

    if debug:
        print(f"\n--- RAW METADATA for {entry.get('name')} ({category}) ---")
        print(json.dumps(entry["metadata"], indent=2)[:2000])
        print("--- END ---\n")

    return entry
