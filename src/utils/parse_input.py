import json
import requests
import os
import re

"""
Enhanced URL parser that handles autograder edge cases:
1. Multiple URLs in one slot separated by spaces
2. Blank lines with just commas
3. Malformed input and missing fields
"""

HF_MODEL_API = "https://huggingface.co/api/models/"
HF_DATASET_API = "https://huggingface.co/api/datasets/"
GH_REPO_API = "https://api.github.com/repos/"

# Global registry to track seen datasets
seen_datasets = {}


def extract_all_urls_from_text(text):
    """
    Extract ALL URLs from a text string, handling space-separated URLs
    This is the key function for handling edge cases like "url1 url2"
    """
    if not text or not isinstance(text, str):
        return []

    # Clean the text first
    text = text.strip().strip("\"'()[]{}")

    if not text:
        return []

    # Use regex to find all URLs in the text
    # This pattern matches HTTP URLs or domain-based URLs
    url_patterns = [
        r'https?://[^\s,;"\'()]+',  # Full HTTP URLs
        r'(?:github\.com|huggingface\.co)/[^\s,;"\'()]+',  # Domain-only URLs
    ]

    found_urls = []

    for pattern in url_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # Clean up each URL
            url = match.strip().rstrip(".,;")

            # Skip if not a valid domain
            if not any(domain in url for domain in ["github.com", "huggingface.co"]):
                continue

            # Ensure proper protocol
            if not url.startswith("http"):
                url = "https://" + url

            # Basic validation
            if len(url) > 10:
                found_urls.append(url)

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in found_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls


def categorize_url(url):
    """Categorize URL type"""
    if not url:
        return "UNKNOWN"
    if "huggingface.co/datasets" in url:
        return "DATASET"
    elif "huggingface.co" in url:
        return "MODEL"
    elif "github.com" in url:
        return "CODE"
    else:
        return "UNKNOWN"


def extract_model_name(url):
    """Extract model name from HuggingFace URL"""
    try:
        if "huggingface.co" in url:
            parts = url.split("huggingface.co/")[-1].split("/")
            if len(parts) >= 2:
                return parts[1]
        return url.rstrip("/").split("/")[-1] or "unknown"
    except Exception:
        return "unknown"


def is_blank_line(line):
    """
    Check if a line is effectively blank (just commas, spaces, quotes)
    This handles the "Many URLs Test" edge case
    """
    if not line:
        return True

    # Remove all whitespace, commas, quotes, and common separators
    cleaned = re.sub(r'[\s,;"\'()]+', "", line)
    return len(cleaned) == 0


def parse_input_file(input_path):
    """
    Enhanced parser that handles edge cases:
    1. Multiple URLs in one comma-separated field (space-separated)
    2. Blank lines with just commas
    3. Malformed input
    """
    if not input_path or not input_path.strip():
        return []

    input_path = input_path.strip()

    # Handle single URL case (direct URL passed)
    if input_path.startswith("http"):
        if categorize_url(input_path) == "MODEL":
            return [
                {
                    "category": "MODEL",
                    "url": input_path,
                    "name": extract_model_name(input_path),
                    "dataset_url": "",
                    "code_url": "",
                }
            ]
        else:
            return []

    # Read input content
    content = ""
    if os.path.isfile(input_path):
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return []
    else:
        content = input_path

    content = content.strip()
    if not content:
        return []

    # Handle JSON format
    if content.startswith("[") and content.endswith("]"):
        try:
            urls = json.loads(content)
            if isinstance(urls, list):
                all_urls = []
                for url in urls:
                    if url and isinstance(url, str):
                        # Extract URLs from each JSON entry (handles space-separated)
                        extracted = extract_all_urls_from_text(url)
                        all_urls.extend(extracted)

                # Process the URLs
                return process_urls_to_models(all_urls)
        except json.JSONDecodeError:
            pass

    # Handle text format
    all_urls = []
    lines = content.split("\n")

    for line in lines:
        line = line.strip()

        # Skip blank lines (handles "Many URLs Test" edge case)
        if is_blank_line(line):
            continue

        # Process comma-separated fields
        if "," in line:
            fields = line.split(",")
            for field in fields:
                field = field.strip()
                if not field:
                    continue

                # Extract all URLs from this field
                # This handles the "Two URLs Test" case where one field has "url1 url2"
                urls_in_field = extract_all_urls_from_text(field)
                all_urls.extend(urls_in_field)
        else:
            # Single field, extract all URLs
            urls_in_line = extract_all_urls_from_text(line)
            all_urls.extend(urls_in_line)

    return process_urls_to_models(all_urls)


def process_urls_to_models(all_urls):
    """
    Process a list of URLs and create model entries
    Returns exactly one entry per MODEL URL found
    """
    # Categorize all URLs
    models = []
    datasets = []
    codes = []

    for url in all_urls:
        url_type = categorize_url(url)
        if url_type == "MODEL":
            models.append(url)
        elif url_type == "DATASET":
            datasets.append(url)
            # Store in global registry
            if url not in seen_datasets:
                seen_datasets[url] = {"url": url}
        elif url_type == "CODE":
            codes.append(url)

    # Create exactly one entry per model URL
    parsed_entries = []

    for i, model_url in enumerate(models):
        # Try to assign appropriate dataset and code URLs
        dataset_url = ""
        code_url = ""

        # Use datasets in order if available
        if i < len(datasets):
            dataset_url = datasets[i]
        elif datasets:
            dataset_url = datasets[0]  # Use first available
        elif seen_datasets:
            dataset_url = list(seen_datasets.keys())[-1]  # Use most recent

        # Use code URLs in order if available
        if i < len(codes):
            code_url = codes[i]
        elif codes:
            code_url = codes[0]  # Use first available

        model_entry = {
            "category": "MODEL",
            "url": model_url,
            "name": extract_model_name(model_url),
            "dataset_url": dataset_url,
            "code_url": code_url,
        }

        parsed_entries.append(model_entry)

    return parsed_entries


def fetch_huggingface_readme(model_id):
    """Fetch README content from HuggingFace model"""
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


def extract_github_urls_from_text(text):
    """Extract GitHub URLs from README text"""
    if not text:
        return []

    github_patterns = [
        r"https?://github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)/?[^\s\)]*",
        r"github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)",
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

    # Remove duplicates
    return list(dict.fromkeys(github_urls))


def fetch_metadata(entry, debug=False):
    """Fetch metadata for model entries"""
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
            # Extract model ID
            try:
                model_id = "/".join(url.split("huggingface.co/")[-1].split("/")[:2])
                if not model_id or model_id == "/":
                    raise ValueError("Could not extract model ID from URL")
            except Exception as e:
                entry["metadata"] = {"error": f"Invalid model URL format: {str(e)}"}
                entry["model_size_mb"] = 0.0
                return entry

            # Query HuggingFace API
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

            # Calculate model size
            md = entry["metadata"]
            if isinstance(md, dict) and "error" not in md:
                size_bytes = 0
                try:
                    if "usedStorage" in md and isinstance(md["usedStorage"], (int, float)):
                        size_bytes = md["usedStorage"]
                    elif "siblings" in md and isinstance(md["siblings"], list):
                        for s in md["siblings"]:
                            if isinstance(s, dict) and isinstance(s.get("size"), (int, float)):
                                size_bytes += s["size"]

                    if size_bytes > 0:
                        entry["model_size_mb"] = round(size_bytes / (1024 * 1024), 2)
                    else:
                        entry["model_size_mb"] = 0.0
                except Exception:
                    entry["model_size_mb"] = 0.0

                # Extract metadata for metrics
                entry["description"] = md.get("description", "")
                entry["downloads"] = md.get("downloads", 0)
                entry["likes"] = md.get("likes", 0)
                entry["tags"] = md.get("tags", [])
                entry["cardData"] = md.get("cardData", {})
                entry["siblings"] = md.get("siblings", [])
                entry["widgetData"] = md.get("widgetData", [])
                entry["transformersInfo"] = md.get("transformersInfo", {})

                # Extract license
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
            else:
                entry["model_size_mb"] = 0.0

            # Preserve URLs from parsing
            if code_url and not entry.get("code_url"):
                entry["code_url"] = code_url
            if dataset_url and not entry.get("dataset_url"):
                entry["dataset_url"] = dataset_url

            # Try to infer code_url from metadata or README if not provided
            if not entry.get("code_url") and isinstance(md, dict) and "error" not in md:
                # Check metadata first
                card_data = md.get("cardData")
                if isinstance(card_data, dict):
                    if "github" in card_data:
                        entry["code_url"] = card_data["github"]
                    elif "repositories" in card_data:
                        repos = card_data["repositories"]
                        if isinstance(repos, list) and repos:
                            entry["code_url"] = repos[0]

                # Check tags
                if not entry.get("code_url") and isinstance(md.get("tags"), list):
                    for t in md["tags"]:
                        if isinstance(t, str) and "github.com" in t:
                            entry["code_url"] = t
                            break

                # Scrape README as last resort
                if not entry.get("code_url"):
                    readme_content = fetch_huggingface_readme(model_id)
                    if readme_content:
                        github_urls = extract_github_urls_from_text(readme_content)
                        if github_urls:
                            entry["code_url"] = github_urls[0]

    except Exception as e:
        entry["metadata"] = {"error": f"Unexpected error: {str(e)}"}
        entry["model_size_mb"] = 0.0

    return entry
