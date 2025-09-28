import json
import requests
import os
import re

"""
Minimal fix to handle edge cases while preserving working behavior
Only adds space-separated URL handling and blank line filtering
"""

HF_MODEL_API = "https://huggingface.co/api/models/"
HF_DATASET_API = "https://huggingface.co/api/datasets/"
GH_REPO_API = "https://api.github.com/repos/"

# Global registry to track seen datasets
seen_datasets = {}


def extract_space_separated_urls(text):
    """
    MINIMAL ADDITION: Extract space-separated URLs from a single field
    Only for handling the "Two URLs Test" edge case
    """
    if not text or not isinstance(text, str):
        return [text] if text else []

    # If text contains space and multiple URLs, split them
    if " " in text and text.count("http") > 1:
        # Use regex to find all URLs
        urls = re.findall(r"https?://[^\s]+", text)
        return [url.strip() for url in urls if url.strip()]

    # Otherwise return as-is
    return [text.strip()] if text.strip() else []


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


def is_model_url(url):
    """Check if URL is a HuggingFace model"""
    return bool(url and "huggingface.co" in url and "/datasets/" not in url)


def is_dataset_url(url):
    """Check if URL is a HuggingFace dataset"""
    return bool(url) and "huggingface.co/datasets" in url


def is_blank_line(line):
    """
    MINIMAL ADDITION: Check if line is effectively blank
    For handling "Many URLs Test" edge case
    """
    if not line:
        return True
    # Remove commas, spaces, quotes
    cleaned = re.sub(r'[\s,"\'\(\)]+', "", line)
    return len(cleaned) == 0


def parse_input_file(input_path):
    """
    Enhanced parser with MINIMAL changes to handle edge cases
    Preserves original logic as much as possible
    """
    if not input_path or not input_path.strip():
        return []

    input_path = input_path.strip()

    # Handle single URL case (direct URL passed)
    if input_path.startswith("http"):
        if is_model_url(input_path):
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
                        # MINIMAL CHANGE: Handle space-separated URLs in JSON
                        extracted = extract_space_separated_urls(url)
                        all_urls.extend(extracted)

                # Process URLs with original logic
                return process_urls_original_logic(all_urls)
        except json.JSONDecodeError:
            pass

    # Handle text format with MINIMAL changes
    all_urls = []
    lines = content.split("\n")

    for line in lines:
        line = line.strip()

        # MINIMAL ADDITION: Skip blank lines
        if is_blank_line(line):
            continue

        # Original comma-splitting logic
        if "," in line:
            parts = line.split(",")
            for part in parts:
                part = part.strip().strip("\"'")
                if not part:
                    continue

                # MINIMAL CHANGE: Handle space-separated URLs in each part
                extracted_urls = extract_space_separated_urls(part)
                all_urls.extend(extracted_urls)
        else:
            # MINIMAL CHANGE: Handle space-separated URLs in single line
            extracted_urls = extract_space_separated_urls(line)
            all_urls.extend(extracted_urls)

    return process_urls_original_logic(all_urls)


def process_urls_original_logic(all_urls):
    """
    PRESERVE ORIGINAL LOGIC: Process URLs exactly like before
    """
    # Categorize URLs (original logic)
    models = []
    datasets = []
    codes = []

    for url in all_urls:
        if not url:
            continue

        if is_model_url(url):
            models.append(url)
        elif is_dataset_url(url):
            datasets.append(url)
            if url not in seen_datasets:
                seen_datasets[url] = {"url": url}
        elif "github.com" in url:
            codes.append(url)

    # Create model entries (original logic)
    parsed_entries = []

    for i, model_url in enumerate(models):
        dataset_url = ""
        code_url = ""

        # Original assignment logic
        if i < len(datasets):
            dataset_url = datasets[i]
        elif datasets:
            dataset_url = datasets[0]
        elif seen_datasets:
            dataset_url = list(seen_datasets.keys())[-1]

        if i < len(codes):
            code_url = codes[i]
        elif codes:
            code_url = codes[0]

        model_entry = {
            "category": "MODEL",
            "url": model_url,
            "name": extract_model_name(model_url),
            "dataset_url": dataset_url,
            "code_url": code_url,
        }

        parsed_entries.append(model_entry)

    return parsed_entries


# PRESERVE ALL ORIGINAL FUNCTIONS BELOW


def fetch_huggingface_readme(model_id):
    """Fetch README content from HuggingFace model"""
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

    return list(dict.fromkeys(github_urls))


def fetch_metadata(entry, debug=False):
    """PRESERVE ORIGINAL metadata fetching logic"""
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

            # Calculate model size (original logic)
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

                # Extract metadata (original logic)
                entry["description"] = md.get("description", "")
                entry["downloads"] = md.get("downloads", 0)
                entry["likes"] = md.get("likes", 0)
                entry["tags"] = md.get("tags", [])
                entry["cardData"] = md.get("cardData", {})
                entry["siblings"] = md.get("siblings", [])
                entry["widgetData"] = md.get("widgetData", [])
                entry["transformersInfo"] = md.get("transformersInfo", {})

                # Extract license (original logic)
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

            # Preserve URLs (original logic)
            if code_url and not entry.get("code_url"):
                entry["code_url"] = code_url
            if dataset_url and not entry.get("dataset_url"):
                entry["dataset_url"] = dataset_url

            # Try to infer code_url (original logic)
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

    except Exception as e:
        entry["metadata"] = {"error": f"Unexpected error: {str(e)}"}
        entry["model_size_mb"] = 0.0

    return entry
