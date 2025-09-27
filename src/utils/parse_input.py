import json
import requests
import os
import re
import logging
from typing import Optional, List, Dict, Any

HF_MODEL_API = "https://huggingface.co/api/models/"
HF_DATASET_API = "https://huggingface.co/api/datasets/"
GH_REPO_API = "https://api.github.com/repos/"

logger = logging.getLogger(__name__)

# Global registry to track seen datasets
seen_datasets: Dict[str, Dict[str, Any]] = {}


def extract_github_urls_from_text(text: str) -> List[str]:
    if not text:
        return []

    github_patterns = [
        r"https?://github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)/?[^\s\)]*",
        r"github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)",
        r"\[.*?\]\(https?://github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)[^\)]*\)",
    ]

    github_urls = []
    for pattern in github_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                if match:
                    url = f"https://github.com/{match[0] if isinstance(match[0], str) else match}"
            else:
                url = match if match.startswith("http") else f"https://github.com/{match}"

            url = url.split("#")[0].split("?")[0].rstrip("/")
            if "/blob/" in url or "/tree/" in url or "/issues" in url:
                continue
            parts = url.replace("https://github.com/", "").split("/")
            if len(parts) >= 2 and parts[0] and parts[1]:
                github_urls.append(url)

    seen_set = set()
    unique = []
    for u in github_urls:
        if u not in seen_set:
            seen_set.add(u)
            unique.append(u)
    return unique


def fetch_huggingface_readme(model_id: str) -> Optional[str]:
    try:
        readme_url = f"https://huggingface.co/{model_id}/raw/main/README.md"
        resp = requests.get(readme_url, timeout=10)
        if resp.status_code == 200:
            return resp.text
        for readme_name in ["README.rst", "readme.md", "readme.txt", "README"]:
            alt_url = f"https://huggingface.co/{model_id}/raw/main/{readme_name}"
            resp = requests.get(alt_url, timeout=5)
            if resp.status_code == 200:
                return resp.text
    except Exception as e:
        logger.debug(f"README fetch failed for {model_id}: {e}")
    return None


def parse_input_file(input_path: str) -> List[Dict[str, str]]:
    """
    Robust parsing:
    - Accepts file path, single direct URL, or JSON array of URLs.
    - For each line, consider *all* comma-separated URLs:
      * Hugging Face dataset -> dataset_url
      * Hugging Face model   -> yields an entry
      * GitHub repo          -> code_url
    - If multiple models appear on a line, emit one entry per model, each
      carrying the dataset/code found on that same line (or last seen dataset fallback).
    - No prints to stdout. All diagnostics go to logger.
    """
    parsed_entries: List[Dict[str, str]] = []

    if not input_path or not input_path.strip():
        logger.warning("Empty or None input provided to parse_input_file")
        return []

    input_path = input_path.strip()

    # Handle single direct URL
    if input_path.startswith("http"):
        # Direct URL: categorize and emit if it's a model
        ds_url = ""
        code_url = ""
        if is_dataset_url(input_path):
            seen_datasets[input_path] = {"url": input_path, "line": 0}
            return []  # dataset alone doesn't produce an entry
        if "github.com" in input_path:
            # code URL alone doesn't produce an entry
            return []
        if is_model_url(input_path):
            if seen_datasets:
                ds_url = list(seen_datasets.keys())[-1]
            parsed_entries.append(make_entry(code_url, ds_url, input_path))
        return parsed_entries

    # Load lines from file or treat input as literal line
    lines: List[str] = []
    if os.path.isfile(input_path):
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
        except Exception as e:
            logger.error(f"Error reading file {input_path}: {e}")
            return []

        if content.startswith("[") and content.endswith("]"):
            # JSON array of URLs
            try:
                urls = json.loads(content)
                if isinstance(urls, list):
                    # treat as a single "line" containing all URLs
                    lines = [",".join([u for u in urls if isinstance(u, str)])]
                else:
                    logger.error(f"Top-level JSON in {input_path} is not a list.")
                    return []
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {input_path}: {e}")
                return []
        else:
            # Plain text lines
            lines = [ln.strip() for ln in content.split("\n") if ln.strip()]
    else:
        # Treat input as a literal "line" of URLs
        lines = [input_path]

    for line_num, line in enumerate(lines, 1):
        # Split and clean every token; do NOT stop early
        raw_parts = line.split(",")
        parts = [p.strip().strip('"').strip("'") for p in raw_parts]
        parts = [p for p in parts if p]  # drop empty tokens only

        dataset_url_on_line = ""
        code_url_on_line = ""
        models_on_line: List[str] = []

        for url in parts:
            if is_dataset_url(url):
                dataset_url_on_line = url
                seen_datasets[url] = {"url": url, "line": line_num}
            elif is_model_url(url):
                models_on_line.append(url)
            elif "github.com" in url:
                code_url_on_line = url
            else:
                # Unknown/unsupported URL type -> ignore silently
                logger.debug(
                    f"Ignoring non-model non-dataset non-GitHub URL on line {line_num}: {url}"
                )

        # Fallback to last seen dataset if none on this line
        if not dataset_url_on_line and seen_datasets:
            dataset_url_on_line = list(seen_datasets.keys())[-1]

        # Emit one entry per model found on this line
        for m in models_on_line:
            parsed_entries.append(make_entry(code_url_on_line, dataset_url_on_line, m))

    return parsed_entries


def make_entry(code_url: str, dataset_url: str, model_url: str) -> Dict[str, str]:
    return {
        "category": "MODEL",
        "url": model_url,
        "name": extract_model_name(model_url),
        "dataset_url": dataset_url,
        "code_url": code_url,
    }


def extract_model_name(url: str) -> str:
    try:
        if "huggingface.co" in url:
            parts = url.split("huggingface.co/")[-1].split("/")
            if len(parts) >= 2:
                return parts[1]
        return url.rstrip("/").split("/")[-1] or "unknown"
    except Exception:
        return "unknown"


def is_model_url(url: str) -> bool:
    return bool(url and "huggingface.co" in url and "/datasets/" not in url)


def is_dataset_url(url: str) -> bool:
    return bool(url) and "huggingface.co/datasets" in url


def fetch_metadata(entry: Dict[str, Any], debug: bool = False) -> Dict[str, Any]:
    category = entry.get("category", "UNKNOWN")
    url = entry.get("url", "")
    code_url = entry.get("code_url", "")
    dataset_url = entry.get("dataset_url", "")

    entry["metadata"] = {}

    if not url or not isinstance(url, str):
        entry["metadata"] = {"error": "Invalid or missing URL"}
        return entry

    try:
        if category == "MODEL":
            # Extract model id
            try:
                model_id = "/".join(url.split("huggingface.co/")[-1].split("/")[:2])
                if not model_id or model_id == "/":
                    raise ValueError("Could not extract model ID from URL")
            except Exception as e:
                entry["metadata"] = {"error": f"Invalid model URL format: {str(e)}"}
                entry["model_size_mb"] = 0.0
                return entry

            # HF API
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
                            if isinstance(s, dict) and isinstance(s.get("size"), (int, float)):
                                size_bytes += s["size"]
                    entry["model_size_mb"] = (
                        round(size_bytes / (1024 * 1024), 2) if size_bytes > 0 else 0.0
                    )
                except Exception as e:
                    entry["model_size_mb"] = 0.0
                    if debug:
                        logger.debug(f"Error calculating model size: {e}")

                # License extraction
                license_found = False
                if isinstance(md.get("license"), str):
                    entry["license"] = md["license"]
                    license_found = True

                card_data = md.get("cardData")
                if not license_found and isinstance(card_data, dict) and "license" in card_data:
                    entry["license"] = card_data["license"]
                    license_found = True

                tags = md.get("tags")
                if not license_found and isinstance(tags, list):
                    for t in tags:
                        if isinstance(t, str) and t.lower().startswith("license:"):
                            entry["license"] = t.split(":", 1)[1].strip()
                            license_found = True
                            break

                # Extra info
                entry["description"] = md.get("description", "")
                entry["downloads"] = md.get("downloads", 0)
                entry["likes"] = md.get("likes", 0)
                entry["tags"] = md.get("tags", [])
                entry["cardData"] = md.get("cardData", {})
                entry["siblings"] = md.get("siblings", [])
                entry["widgetData"] = md.get("widgetData", [])
                entry["transformersInfo"] = md.get("transformersInfo", {})

            if not entry.get("code_url") and code_url:
                entry["code_url"] = code_url
            if not entry.get("dataset_url") and dataset_url:
                entry["dataset_url"] = dataset_url

            if not entry.get("code_url") and isinstance(md, dict) and "error" not in md:
                card_data = md.get("cardData")
                if isinstance(card_data, dict):
                    if "github" in card_data:
                        entry["code_url"] = card_data["github"]
                    elif "repositories" in card_data:
                        repos = card_data["repositories"]
                        if isinstance(repos, list) and repos:
                            entry["code_url"] = repos[0]
                if not entry.get("code_url") and isinstance(md.get("tags"), list):
                    for t in md["tags"]:
                        if isinstance(t, str) and "github.com" in t:
                            entry["code_url"] = t
                            break

            if not entry.get("code_url"):
                if debug:
                    logger.debug(f"Scraping README for {model_id} to find GitHub URLs...")
                readme_content = fetch_huggingface_readme(model_id)
                if readme_content:
                    github_urls = extract_github_urls_from_text(readme_content)
                    if github_urls:
                        entry["code_url"] = github_urls[0]

    except Exception as e:
        entry["metadata"] = {"error": f"Unexpected error: {str(e)}"}
        entry["model_size_mb"] = 0.0

    if debug:
        logger.debug(
            f"SUMMARY name={entry.get('name', 'unknown')} "
            f"code_url={entry.get('code_url')} dataset_url={entry.get('dataset_url')} "
            f"license={entry.get('license')} size_mb={entry.get('model_size_mb')}"
        )
    return entry
