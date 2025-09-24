import json
import requests
import os
from typing import Optional, List, Dict, Any

"""
Parses input URLs, validates them, and fetches raw metadata.
This file does not calculate metrics — it just collects data
"""

HF_MODEL_API = "https://huggingface.co/api/models/"
HF_DATASET_API = "https://huggingface.co/api/datasets/"
GH_REPO_API = "https://api.github.com/repos/"


def parse_input_file(input_path: str) -> List[Dict[str, str]]:
    """
    Parses input file or URL, validates them, and returns structured MODEL entries only.
    """
    parsed_entries = []

    if not input_path or not input_path.strip():
        print("Warning: Empty or None input provided")
        return []

    input_path = input_path.strip()

    if os.path.isfile(input_path):
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error reading file {input_path}: {e}")
            return []
    else:
        urls = [input_path]

    for url in urls:
        if not url or not url.strip():
            continue

        entry = categorize_url(url)
        # Only return entries that are models
        if entry and entry["category"] == "MODEL":
            parsed_entries.append(entry)

    return parsed_entries


# Added this to check for empty URLS https://piazza.com/class/mea7w9al5bg11j/post/104
def categorize_url(url: str) -> Optional[Dict[str, str]]:
    """
    Categorizes a single URL, only caring about MODEL vs other types.
    """
    if not url or not isinstance(url, str):
        return None

    url = url.strip()
    if not url or "." not in url:
        return None

    try:
        url_parts = url.rstrip("/").split("/")
        name = (
            url_parts[-1] if url_parts[-1] else (url_parts[-2] if len(url_parts) > 1 else "unknown")
        )
    except Exception:
        name = "unknown"

    # Models on Hugging Face
    if "huggingface.co" in url and "datasets" not in url:
        return {"category": "MODEL", "url": url, "name": name}

    # Everything else is ignored
    return None


def fetch_metadata(entry: Dict[str, Any], debug: bool = False) -> Dict[str, Any]:
    """
    Given a parsed entry, validate the URL and fetch metadata from HuggingFace or GitHub APIs.
    Attaches a 'metadata' field to the entry.
    """
    # Use .get() with default to prevent KeyError
    category = entry.get("category", "UNKNOWN")
    url = entry.get("url", "")

    # Initialize metadata as empty dict
    entry["metadata"] = {}

    if not url or not isinstance(url, str):
        entry["metadata"] = {"error": "Invalid or missing URL"}
        return entry

    try:
        if category == "MODEL":
            # Extract model ID more safely
            try:
                model_id = "/".join(url.split("huggingface.co/")[-1].split("/")[:2])
                if not model_id or model_id == "/":
                    raise ValueError("Could not extract model ID from URL")
            except Exception as e:
                entry["metadata"] = {"error": f"Invalid model URL format: {str(e)}"}
                entry["model_size_mb"] = 0.0
                return entry

            try:
                resp = requests.get(HF_MODEL_API + model_id, timeout=10)
                if resp.status_code == 200:
                    entry["metadata"] = resp.json()
                elif resp.status_code == 404:
                    entry["metadata"] = {"error": "Model not found (404)"}
                elif resp.status_code == 403:
                    entry["metadata"] = {"error": "Access forbidden (403)"}
                else:
                    entry["metadata"] = {"error": f"HTTP {resp.status_code}: {resp.reason}"}
            except requests.exceptions.Timeout:
                entry["metadata"] = {"error": "Request timeout"}
            except requests.exceptions.ConnectionError:
                entry["metadata"] = {"error": "Connection error"}
            except requests.exceptions.RequestException as e:
                entry["metadata"] = {"error": f"Request failed: {str(e)}"}

            # Calculate model size safely
            size_bytes = 0
            md = entry["metadata"]

            if not isinstance(md, dict) or "error" in md:
                entry["model_size_mb"] = 0.0
            else:
                try:
                    # usedStorage field
                    if "usedStorage" in md and isinstance(md["usedStorage"], (int, float)):
                        size_bytes = md["usedStorage"]

                    # sum sizes of files in siblings
                    elif "siblings" in md and isinstance(md["siblings"], list):
                        for s in md["siblings"]:
                            if (
                                isinstance(s, dict)
                                and "size" in s
                                and isinstance(s["size"], (int, float))
                            ):
                                size_bytes += s["size"]

                    entry["model_size_mb"] = (
                        round(size_bytes / (1024 * 1024), 2) if size_bytes > 0 else 0.0
                    )
                except Exception as e:
                    entry["model_size_mb"] = 0.0
                    if debug:
                        print(f"Warning: Error calculating model size: {e}")

        elif category == "DATASET":
            # Extract dataset ID more safely
            try:
                dataset_id = "/".join(url.split("huggingface.co/datasets/")[-1].split("/")[:2])
                if not dataset_id or dataset_id == "/":
                    raise ValueError("Could not extract dataset ID from URL")
            except Exception as e:
                entry["metadata"] = {"error": f"Invalid dataset URL format: {str(e)}"}
                entry["dataset_size_mb"] = 0.0
                return entry

            try:
                resp = requests.get(HF_DATASET_API + dataset_id, timeout=10)
                if resp.status_code == 200:
                    entry["metadata"] = resp.json()
                elif resp.status_code == 404:
                    entry["metadata"] = {"error": "Dataset not found (404)"}
                elif resp.status_code == 403:
                    entry["metadata"] = {"error": "Access forbidden (403)"}
                else:
                    entry["metadata"] = {"error": f"HTTP {resp.status_code}: {resp.reason}"}
            except requests.exceptions.Timeout:
                entry["metadata"] = {"error": "Request timeout"}
            except requests.exceptions.ConnectionError:
                entry["metadata"] = {"error": "Connection error"}
            except requests.exceptions.RequestException as e:
                entry["metadata"] = {"error": f"Request failed: {str(e)}"}

            # Calculate dataset size safely
            size_bytes = 0
            md = entry["metadata"]

            if not isinstance(md, dict) or "error" in md:
                entry["dataset_size_mb"] = 0.0
            else:
                try:
                    if "usedStorage" in md and isinstance(md["usedStorage"], (int, float)):
                        size_bytes = md["usedStorage"]
                    elif "siblings" in md and isinstance(md["siblings"], list):
                        for s in md["siblings"]:
                            if (
                                isinstance(s, dict)
                                and "size" in s
                                and isinstance(s["size"], (int, float))
                            ):
                                size_bytes += s["size"]

                    entry["dataset_size_mb"] = (
                        round(size_bytes / (1024 * 1024), 2) if size_bytes > 0 else 0.0
                    )
                except Exception as e:
                    entry["dataset_size_mb"] = 0.0
                    if debug:
                        print(f"Warning: Error calculating dataset size: {e}")

        elif category == "CODE":
            # Extract repo path more safely
            try:
                parts = url.split("github.com/")[-1].split("/")
                if len(parts) < 2:
                    raise ValueError("Invalid GitHub URL format")
                repo_path = "/".join(parts[:2])
                if not repo_path or "/" not in repo_path:
                    raise ValueError("Could not extract repository path")
            except Exception as e:
                entry["metadata"] = {"error": f"Invalid GitHub URL format: {str(e)}"}
                entry["repo_size_kb"] = 0
                return entry

            try:
                resp = requests.get(GH_REPO_API + repo_path, timeout=10)
                if resp.status_code == 200:
                    entry["metadata"] = resp.json()
                elif resp.status_code == 404:
                    entry["metadata"] = {"error": "Repository not found (404)"}
                elif resp.status_code == 403:
                    entry["metadata"] = {"error": "Access forbidden (403) - may be rate limited"}
                else:
                    entry["metadata"] = {"error": f"HTTP {resp.status_code}: {resp.reason}"}
            except requests.exceptions.Timeout:
                entry["metadata"] = {"error": "Request timeout"}
            except requests.exceptions.ConnectionError:
                entry["metadata"] = {"error": "Connection error"}
            except requests.exceptions.RequestException as e:
                entry["metadata"] = {"error": f"Request failed: {str(e)}"}

            # Extract repo size safely
            if isinstance(entry["metadata"], dict) and "size" in entry["metadata"]:
                try:
                    size_val = entry["metadata"]["size"]
                    if isinstance(size_val, (int, float)):
                        entry["repo_size_kb"] = int(size_val)
                    else:
                        entry["repo_size_kb"] = 0
                except Exception:
                    entry["repo_size_kb"] = 0
            else:
                entry["repo_size_kb"] = 0

        else:
            # UNKNOWN category
            entry["metadata"] = {"error": f"Unknown category: {category}"}

    except Exception as e:
        entry["metadata"] = {"error": f"Unexpected error: {str(e)}"}
        # Set default size values
        if category == "MODEL":
            entry["model_size_mb"] = 0.0
        elif category == "DATASET":
            entry["dataset_size_mb"] = 0.0
        elif category == "CODE":
            entry["repo_size_kb"] = 0

    if debug:
        print(f"\n--- RAW METADATA for {entry.get('name', 'unknown')} ({category}) ---")
        if isinstance(entry.get("metadata"), dict):
            print(json.dumps(entry["metadata"], indent=2)[:2000])  # show first 2000 chars
        else:
            print("Invalid metadata format")
        print("--- END ---\n")

    return entry
