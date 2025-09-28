import json
import requests
import os
import re
from typing import Optional, List, Dict, Any

"""
Enhanced version that handles all edge cases for URL parsing
"""

HF_MODEL_API = "https://huggingface.co/api/models/"
HF_DATASET_API = "https://huggingface.co/api/datasets/"
GH_REPO_API = "https://api.github.com/repos/"

# Global registry to track seen datasets
seen_datasets: Dict[str, Dict[str, Any]] = {}


def extract_github_urls_from_text(text: str) -> List[str]:
    """
    Extract GitHub repository URLs from text content
    """
    if not text:
        return []

    # Pattern to search for GitHub URLs
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
                # For patterns with groups, reconstruct the URL
                if match:
                    url = f"https://github.com/{match[0] if isinstance(match[0], str) else match}"
            else:
                url = match if match.startswith("http") else f"https://github.com/{match}"

            # Clean up the URL (remove trailing stuff)
            url = url.split("#")[0].split("?")[0].rstrip("/")

            # Validate it looks like a repo URL (owner/repo format)
            if "/blob/" not in url and "/tree/" not in url and "/issues" not in url:
                parts = url.replace("https://github.com/", "").split("/")
                if len(parts) >= 2 and parts[0] and parts[1]:
                    github_urls.append(url)

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in github_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls


def fetch_huggingface_readme(model_id: str) -> Optional[str]:
    """
    Fetch the README content from a Hugging Face model
    """
    try:
        readme_url = f"https://huggingface.co/{model_id}/raw/main/README.md"
        resp = requests.get(readme_url, timeout=10)
        if resp.status_code == 200:
            return resp.text

        # Try alternative README formats
        for readme_name in ["README.rst", "readme.md", "readme.txt", "README"]:
            alt_url = f"https://huggingface.co/{model_id}/raw/main/{readme_name}"
            resp = requests.get(alt_url, timeout=5)
            if resp.status_code == 200:
                return resp.text

    except Exception:
        pass

    return None


def parse_single_url(url: str) -> List[Dict[str, str]]:
    """Handle direct URL input"""
    if is_model_url(url):
        return [
            {
                "category": "MODEL",
                "url": url,
                "name": extract_model_name(url),
                "dataset_url": "",
                "code_url": "",
            }
        ]
    return []


def extract_all_urls_from_line(line: str) -> List[str]:
    """
    Extract all URLs from a line, handling various separators and formats
    """
    urls = []

    # First try comma separation
    comma_parts = [p.strip().strip('"').strip("'") for p in line.split(",")]

    for part in comma_parts:
        if not part:
            continue

        # Check if this part contains multiple space-separated URLs
        space_urls = re.findall(r"https?://[^\s,]+", part)
        if space_urls:
            urls.extend(space_urls)
        elif part.startswith("http") or "huggingface.co" in part:
            # Single URL
            if not part.startswith("http"):
                part = "https://" + part
            urls.append(part)

    # If no URLs found with comma splitting, try space splitting on whole line
    if not urls:
        space_urls = re.findall(r"https?://[^\s,]+", line)
        urls.extend(space_urls)

    return urls


def parse_input_file(input_path: str) -> List[Dict[str, str]]:
    """
    Enhanced parser that handles all edge cases:
    - Single URLs
    - Multiple URLs per line (space or comma separated)
    - JSON format files
    - Text format files
    - Blank/empty lines
    - Lines with 1, 2, or 3+ URLs
    """
    parsed_entries: List[Dict[str, str]] = []

    if not input_path or not input_path.strip():
        return []

    input_path = input_path.strip()

    # Handle single URL case (direct URL passed)
    if input_path.startswith("http"):
        return parse_single_url(input_path)

    # Handle file input
    if not os.path.isfile(input_path):
        return []

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            return []

        # Detect JSON vs TXT format
        if content.startswith("[") and content.endswith("]"):
            # JSON format
            try:
                urls = json.loads(content)
                if not isinstance(urls, list):
                    return []

                # Each URL in the list should produce one model entry
                for url in urls:
                    if url and isinstance(url, str) and is_model_url(url):
                        parsed_entries.extend(parse_single_url(url))

            except json.JSONDecodeError:
                return []
        else:
            # Text format - process line by line
            lines = content.split("\n")

            for line_num, line in enumerate(lines, 1):
                line = line.strip()

                # Skip truly empty lines
                if not line:
                    continue

                # Skip lines that are just punctuation/whitespace
                if re.match(r'^[\s,;"\'()]*$', line):
                    continue

                # Extract all URLs from this line
                all_urls = extract_all_urls_from_line(line)

                if not all_urls:
                    continue

                # Determine code_url, dataset_url, and model_urls based on URL count and types
                code_url = ""
                dataset_url = ""
                model_urls = []

                # Categorize URLs
                for url in all_urls:
                    if is_model_url(url):
                        model_urls.append(url)
                    elif "github.com" in url:
                        if not code_url:  # Use first GitHub URL as code_url
                            code_url = url
                    elif is_dataset_url(url):
                        if not dataset_url:  # Use first dataset URL
                            dataset_url = url

                # If we have model URLs, create entries for them
                for model_url in model_urls:
                    # Handle dataset inheritance from previous lines
                    current_dataset_url = dataset_url
                    if not current_dataset_url and seen_datasets:
                        # Inherit from last seen dataset
                        current_dataset_url = list(seen_datasets.keys())[-1]

                    # Store new dataset if we found one
                    if dataset_url and dataset_url not in seen_datasets:
                        seen_datasets[dataset_url] = {"url": dataset_url, "line": line_num}

                    # Create model entry
                    entry = {
                        "category": "MODEL",
                        "url": model_url,
                        "name": extract_model_name(model_url),
                        "dataset_url": current_dataset_url,
                        "code_url": code_url,
                    }

                    parsed_entries.append(entry)

    except Exception as e:
        print(f"Error reading file {input_path}: {e}")
        return []

    return parsed_entries


def extract_model_name(url: str) -> str:
    """Extract model name from HuggingFace URL"""
    try:
        if "huggingface.co" in url:
            parts = url.split("huggingface.co/")[-1].split("/")
            if len(parts) >= 2:
                return parts[1]  # Get model name (second part after owner)
        # Fallback
        return url.rstrip("/").split("/")[-1] or "unknown"
    except Exception:
        return "unknown"


def is_model_url(url: str) -> bool:
    """Check if URL is a HuggingFace model"""
    return bool(url and "huggingface.co" in url and "/datasets/" not in url)


def is_dataset_url(url: str) -> bool:
    """Check if URL is a HuggingFace dataset"""
    return bool(url) and "huggingface.co/datasets" in url


def fetch_metadata(entry: Dict[str, Any], debug: bool = False) -> Dict[str, Any]:
    """
    Enhanced metadata fetching that scrapes READMEs for GitHub URLs
    """
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
            # Extract model ID safely
            try:
                model_id = "/".join(url.split("huggingface.co/")[-1].split("/")[:2])
                if not model_id or model_id == "/":
                    raise ValueError("Could not extract model ID from URL")
            except Exception as e:
                entry["metadata"] = {"error": f"Invalid model URL format: {str(e)}"}
                entry["model_size_mb"] = 0.0
                return entry

            # Query Hugging Face API
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

            # Size calculation
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
                    if debug:
                        print(f"Warning: Error calculating model size: {e}")

                # Extract license from metadata
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

                # Extract additional info for dataset_and_code metric
                entry["description"] = md.get("description", "")
                entry["downloads"] = md.get("downloads", 0)
                entry["likes"] = md.get("likes", 0)
                entry["tags"] = md.get("tags", [])
                entry["cardData"] = md.get("cardData", {})
                entry["siblings"] = md.get("siblings", [])
                entry["widgetData"] = md.get("widgetData", [])
                entry["transformersInfo"] = md.get("transformersInfo", {})

            # Preserve code_url and dataset_url from input parsing
            if not entry.get("code_url") and code_url:
                entry["code_url"] = code_url

            if not entry.get("dataset_url") and dataset_url:
                entry["dataset_url"] = dataset_url

            # If no code_url yet, try to infer from metadata first
            if not entry.get("code_url") and isinstance(md, dict) and "error" not in md:
                # Try to infer from metadata
                card_data = md.get("cardData")
                if isinstance(card_data, dict):
                    if "github" in card_data:
                        entry["code_url"] = card_data["github"]
                    elif "repositories" in card_data:
                        repos = card_data["repositories"]
                        if isinstance(repos, list) and repos:
                            entry["code_url"] = repos[0]

                # Fallback: look in tags
                if not entry.get("code_url") and isinstance(md.get("tags"), list):
                    for t in md["tags"]:
                        if isinstance(t, str) and "github.com" in t:
                            entry["code_url"] = t
                            break

            # NEW: If still no code_url, scrape the README for GitHub URLs
            if not entry.get("code_url"):
                if debug:
                    print(f"Scraping README for {model_id} to find GitHub URLs...")

                readme_content = fetch_huggingface_readme(model_id)
                if readme_content:
                    github_urls = extract_github_urls_from_text(readme_content)
                    if github_urls:
                        # Use the first GitHub URL found
                        entry["code_url"] = github_urls[0]
                        if debug:
                            print(f"Found GitHub URL in README: {github_urls[0]}")
                    elif debug:
                        print("No GitHub URLs found in README")
                elif debug:
                    print("Could not fetch README")

    except Exception as e:
        entry["metadata"] = {"error": f"Unexpected error: {str(e)}"}
        entry["model_size_mb"] = 0.0

    if debug:
        print(f"\n--- METADATA SUMMARY for {entry.get('name', 'unknown')} ---")
        print(f"Code URL: {entry.get('code_url', 'None')}")
        print(f"Dataset URL: {entry.get('dataset_url', 'None')}")
        print(f"License: {entry.get('license', 'None')}")
        print(f"Size: {entry.get('model_size_mb', 0)} MB")
        if isinstance(entry.get("metadata"), dict) and "error" in entry["metadata"]:
            print(f"Error: {entry['metadata']['error']}")

    return entry
