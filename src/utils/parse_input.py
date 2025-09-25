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


seen_datasets: set[str] = set()  # global dataset registry


def parse_input_file(input_path: str) -> List[Dict[str, str]]:
    """
    Parses input file or URL, validates them, and returns structured MODEL entries.
    Each entry always has fields: url, name, category, dataset_url, code_url.
    Empty string "" means missing dataset/code.
    """
    parsed_entries: List[Dict[str, str]] = []

    if not input_path or not input_path.strip():
        print("Warning: Empty or None input provided")
        return []

    input_path = input_path.strip()

    # If it's a file, read lines; else treat input_path as single line
    if os.path.isfile(input_path):
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error reading file {input_path}: {e}")
            return []
    else:
        lines = [input_path]

    for line in lines:
        # Split into [code, dataset, model] — may contain blanks
        parts = [p.strip() for p in line.split(",")]
        while len(parts) < 3:
            parts.insert(0, "")

        code_url, dataset_url, model_url = parts[-3:]

        if not model_url:
            continue  # must have a model

        model_entry = categorize_url(model_url)
        if not (model_entry and model_entry["category"] == "MODEL"):
            continue

        # Normalize dataset_url
        if dataset_url:
            if dataset_url not in seen_datasets:
                seen_datasets.add(dataset_url)
            model_entry["dataset_url"] = dataset_url
        else:
            model_entry["dataset_url"] = ""  # always str

        # Normalize code_url
        model_entry["code_url"] = code_url if code_url else ""

        parsed_entries.append(model_entry)

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

    # Extract name with special handling for HuggingFace URLs
    try:
        if "huggingface.co" in url and "datasets" not in url:
            # For HuggingFace model URLs, extract the model name properly
            # Format: huggingface.co/owner/model-name[/tree/branch]
            # Had issues with one naming itself main instead of the models name
            parts = url.split("huggingface.co/")[-1].split("/")
            if len(parts) >= 2:
                name = parts[1]  # Get the model name (second part after owner)
            else:
                name = parts[0] if parts else "unknown"
        else:
            # For other URLs, use existing logic
            url_parts = url.rstrip("/").split("/")
            name = (
                url_parts[-1]
                if url_parts[-1]
                else (url_parts[-2] if len(url_parts) > 1 else "unknown")
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
    Attaches a 'metadata' field to the entry and promotes useful fields like license and size.
    """
    category = entry.get("category", "UNKNOWN")
    url = entry.get("url", "")

    # Initialize metadata as empty dict
    entry["metadata"] = {}

    if not url or not isinstance(url, str):
        entry["metadata"] = {"error": "Invalid or missing URL"}
        return entry

    try:
        if category == "MODEL":
            # Extract model ID safely
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

                    entry["model_size_mb"] = (
                        round(size_bytes / (1024 * 1024), 2) if size_bytes > 0 else 0.0
                    )
                except Exception as e:
                    entry["model_size_mb"] = 0.0
                    if debug:
                        print(f"Warning: Error calculating model size: {e}")

                # Extract license from Hugging Face metadata
                if "license" in md and isinstance(md["license"], str):
                    entry["license"] = md["license"]
                elif "cardData" in md and isinstance(md["cardData"], dict):
                    if "license" in md["cardData"]:
                        entry["license"] = md["cardData"]["license"]
                if "tags" in md and isinstance(md["tags"], list):
                    for t in md["tags"]:
                        if isinstance(t, str) and t.lower().startswith("license:"):
                            entry["license"] = t.split(":", 1)[1].strip()

        elif category == "DATASET":
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

            # Extract license and size from GitHub metadata
            if isinstance(entry["metadata"], dict):
                md = entry["metadata"]
                if "license" in md and isinstance(md["license"], dict):
                    spdx = md["license"].get("spdx_id")
                    if spdx and spdx != "NOASSERTION":
                        entry["license"] = spdx
                    elif "name" in md["license"]:
                        entry["license"] = md["license"]["name"]
                # Extract repo size
                if "size" in md:
                    try:
                        size_val = md["size"]
                        if isinstance(size_val, (int, float)):
                            entry["repo_size_kb"] = int(size_val)
                        else:
                            entry["repo_size_kb"] = 0
                    except Exception:
                        entry["repo_size_kb"] = 0
                else:
                    entry["repo_size_kb"] = 0

        else:
            entry["metadata"] = {"error": f"Unknown category: {category}"}

    except Exception as e:
        entry["metadata"] = {"error": f"Unexpected error: {str(e)}"}
        if category == "MODEL":
            entry["model_size_mb"] = 0.0
        elif category == "DATASET":
            entry["dataset_size_mb"] = 0.0
        elif category == "CODE":
            entry["repo_size_kb"] = 0

    if debug:
        print(f"\n--- RAW METADATA for {entry.get('name', 'unknown')} ({category}) ---")
        if isinstance(entry.get("metadata"), dict):
            print(json.dumps(entry["metadata"], indent=2)[:2000])
        else:
            print("Invalid metadata format")
        print("--- END ---\n")

    return entry
