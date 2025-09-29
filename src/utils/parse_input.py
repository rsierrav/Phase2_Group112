import json
import requests
import os
import re
import logging
from typing import Optional, List, Dict, Any

"""
Enhanced version that scrapes model READMEs to find GitHub repository links
"""

HF_MODEL_API = "https://huggingface.co/api/models/"
HF_DATASET_API = "https://huggingface.co/api/datasets/"
GH_REPO_API = "https://api.github.com/repos/"

seen_datasets: Dict[str, Dict[str, Any]] = {}


def extract_github_urls_from_text(text: str) -> List[str]:
    logging.debug("Extracting GitHub URLs from text")
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
            if "/blob/" not in url and "/tree/" not in url and "/issues" not in url:
                parts = url.replace("https://github.com/", "").split("/")
                if len(parts) >= 2 and parts[0] and parts[1]:
                    github_urls.append(url)

    seen = set()
    unique_urls = []
    for url in github_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    logging.debug(f"Found {len(unique_urls)} unique GitHub URLs")
    return unique_urls


def fetch_huggingface_readme(model_id: str) -> Optional[str]:
    logging.debug(f"Fetching README for Hugging Face model: {model_id}")
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
        logging.warning(f"Failed to fetch README for {model_id}: {e}")
    return None


def parse_input_file(input_path: str) -> List[Dict[str, str]]:
    logging.info(f"Parsing input file or URL: {input_path}")
    parsed_entries: List[Dict[str, str]] = []

    if not input_path or not input_path.strip():
        logging.warning("Empty or None input provided to parse_input_file")
        return []

    input_path = input_path.strip()
    if input_path.startswith("http"):
        if "huggingface.co" in input_path and "/datasets/" not in input_path:
            entry = {
                "category": "MODEL",
                "url": input_path,
                "name": extract_model_name(input_path),
                "dataset_url": "",
                "code_url": "",
            }
            logging.debug(f"Direct URL parsed as MODEL: {entry}")
            return [entry]
        else:
            logging.info("Non-model direct URL provided, skipping")
            return []

    lines = []
    if os.path.isfile(input_path):
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content.startswith("[") and content.endswith("]"):
                try:
                    urls = json.loads(content)
                    if isinstance(urls, list):
                        for url in urls:
                            if url and is_model_url(url):
                                lines.append(f",,{url}")
                except json.JSONDecodeError as e:
                    logging.error(f"Invalid JSON format in {input_path}: {e}")
                    return []
            else:
                lines = [line.strip() for line in content.split("\n") if line.strip()]
        except Exception as e:
            logging.error(f"Error reading file {input_path}: {e}", exc_info=True)
            return []
    else:
        lines = [input_path]

    for line_num, line in enumerate(lines, 1):
        if not line.strip():
            continue
        parts = [p.strip().strip('"').strip("'") for p in line.split(",")]
        while len(parts) < 3:
            parts.append("")
        code_url, dataset_url, model_url = parts[0], parts[1], parts[2]
        if not model_url or not is_model_url(model_url):
            continue
        if dataset_url and is_dataset_url(dataset_url):
            if dataset_url not in seen_datasets:
                seen_datasets[dataset_url] = {"url": dataset_url, "line": line_num}
        elif not dataset_url and seen_datasets:
            inferred_dataset = list(seen_datasets.keys())[-1]
            dataset_url = inferred_dataset
        model_entry = {
            "category": "MODEL",
            "url": model_url,
            "name": extract_model_name(model_url),
            "dataset_url": dataset_url,
            "code_url": code_url,
        }
        logging.debug(f"Parsed model entry (line {line_num}): {model_entry}")
        parsed_entries.append(model_entry)

    logging.info(f"Finished parsing input, found {len(parsed_entries)} MODEL entries")
    return parsed_entries


def categorize_url(url: str) -> Optional[Dict[str, str]]:
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    if not url or "." not in url:
        return None
    try:
        if "huggingface.co" in url and "datasets" not in url:
            parts = url.split("huggingface.co/")[-1].split("/")
            if len(parts) >= 2:
                name = parts[1]
            else:
                name = parts[0] if parts else "unknown"
        else:
            url_parts = url.rstrip("/").split("/")
            name = url_parts[-1] if url_parts[-1] else (url_parts[-2] if len(url_parts) > 1 else "unknown")
    except Exception:
        name = "unknown"

    if "huggingface.co" in url and "datasets" not in url:
        logging.debug(f"URL categorized as MODEL: {url}")
        return {"category": "MODEL", "url": url, "name": name}
    return None


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
    logging.info(f"Fetching metadata for {entry.get('name', 'unknown')} ({url})")

    entry["metadata"] = {}
    if not url or not isinstance(url, str):
        entry["metadata"] = {"error": "Invalid or missing URL"}
        logging.error("Invalid or missing URL in fetch_metadata")
        return entry

    try:
        if category == "MODEL":
            try:
                model_id = "/".join(url.split("huggingface.co/")[-1].split("/")[:2])
                if not model_id or model_id == "/":
                    raise ValueError("Could not extract model ID from URL")
            except Exception as e:
                entry["metadata"] = {"error": f"Invalid model URL format: {e}"}
                entry["model_size_mb"] = 0.0
                logging.error(f"Failed extracting model ID from {url}: {e}")
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
                entry["metadata"] = {"error": f"Request failed: {e}"}

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
                    entry["model_size_mb"] = round(size_bytes / (1024 * 1024), 2) if size_bytes > 0 else 0.0
                except Exception as e:
                    entry["model_size_mb"] = 0.0
                    logging.warning(f"Error calculating model size for {url}: {e}")

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

                entry["description"] = md.get("description", "")
                entry["downloads"] = md.get("downloads", 0)
                entry["likes"] = md.get("likes", 0)
                entry["tags"] = md.get("tags", [])
                entry["cardData"] = md.get("cardData", {})
                entry["siblings"] = md.get("siblings", [])
                entry["widgetData"] = md.get("widgetData", [])
                entry["transformersInfo"] = md.get("transformersInfo", {})

            if not entry.get("code_url"):
                entry["code_url"] = entry.get("code_url", "")
            if not entry.get("dataset_url"):
                entry["dataset_url"] = entry.get("dataset_url", "")

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
                readme_content = fetch_huggingface_readme(model_id)
                if readme_content:
                    github_urls = extract_github_urls_from_text(readme_content)
                    if github_urls:
                        entry["code_url"] = github_urls[0]
                        logging.debug(f"Found GitHub URL in README for {url}: {github_urls[0]}")

    except Exception as e:
        entry["metadata"] = {"error": f"Unexpected error: {str(e)}"}
        entry["model_size_mb"] = 0.0
        logging.error(f"Unexpected error in fetch_metadata for {url}: {e}", exc_info=True)

    logging.info(f"Finished metadata fetch for {entry.get('name', 'unknown')}")
    return entry
