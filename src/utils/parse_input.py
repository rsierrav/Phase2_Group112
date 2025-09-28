import json
import requests
import os
import re
from typing import Optional, List, Dict, Any

"""
Enhanced version that scrapes model READMEs to find GitHub repository links
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

    return unique_urls


def fetch_huggingface_readme(model_id: str) -> Optional[str]:
    """Fetch the README content from a Hugging Face model"""
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


# --- Helpers for parsing ------------------------------------------------------

_URL_TOKEN_RE = re.compile(
    r"(https?://[^\s,;|]+|(?:github\.com|huggingface\.co)/[^\s,;|]+)",
    flags=re.IGNORECASE,
)


def _ensure_https(url: str) -> str:
    url = url.strip().strip("\"'")

    if not url:
        return url

    if not url.lower().startswith(("http://", "https://")):
        if url.lower().startswith(("github.com/", "huggingface.co/")):
            url = "https://" + url
    return url


def _normalize_github_repo_url(url: str) -> str:
    url = _ensure_https(url)
    if "github.com/" not in url.lower():
        return url

    base = url.split("#")[0].split("?")[0]
    tail = base.split("github.com/")[-1]
    parts = [p for p in tail.split("/") if p]

    if len(parts) >= 2:
        owner, repo = parts[0], parts[1]
        return f"https://github.com/{owner}/{repo}"
    return url


def _normalize_hf_model_url(url: str) -> str:
    url = _ensure_https(url)
    if "huggingface.co/" not in url.lower():
        return url
    if "/datasets/" in url.lower():
        return url

    base = url.split("#")[0].split("?")[0]
    tail = base.split("huggingface.co/")[-1]
    parts = [p for p in tail.split("/") if p]

    if len(parts) >= 2:
        owner, model = parts[0], parts[1]
        return f"https://huggingface.co/{owner}/{model}"
    return base.rstrip("/")


def _normalize_hf_dataset_url(url: str) -> str:
    url = _ensure_https(url)
    low = url.lower()
    if "huggingface.co/datasets/" not in low:
        return url

    base = url.split("#")[0].split("?")[0]
    tail = base.split("huggingface.co/datasets/")[-1]
    parts = [p for p in tail.split("/") if p]

    if len(parts) == 1:
        return f"https://huggingface.co/datasets/{parts[0]}"
    elif len(parts) >= 2:
        return f"https://huggingface.co/datasets/{parts[0]}/{parts[1]}"
    return "https://huggingface.co/datasets"


def _classify_and_normalize(url: str):
    u = _ensure_https(url)
    low = u.lower()

    if "github.com/" in low:
        return "code", _normalize_github_repo_url(u)
    if "huggingface.co/datasets/" in low:
        return "dataset", _normalize_hf_dataset_url(u)
    if "huggingface.co/" in low and "/datasets/" not in low:
        return "model", _normalize_hf_model_url(u)
    return None, u


def _line_is_effectively_blank(line: str) -> bool:
    return re.fullmatch(r'[\s,;"\'()]*', line or "") is not None


def parse_input_file(input_path: str) -> List[Dict[str, str]]:
    """
    Parses input with messy lines:
      - Proper 3-field CSV (code_url, dataset_url, model_url)
      - Lines with 2 or many URLs in any order (space/comma separated)
      - Blank/garbage lines like ",,,"
    Returns one MODEL entry per model URL found on a line, attaching the best
    dataset/code URLs found on that same line. If no dataset on the line,
    reuses the most recently seen dataset.
    """
    parsed_entries: List[Dict[str, str]] = []

    if not input_path or not input_path.strip():
        print("Warning: Empty or None input provided")
        return []

    input_path = input_path.strip()

    if input_path.startswith("http"):
        kind, norm = _classify_and_normalize(input_path)
        if kind == "model":
            return [
                {
                    "category": "MODEL",
                    "url": norm,
                    "name": extract_model_name(norm),
                    "dataset_url": "",
                    "code_url": "",
                }
            ]
        else:
            return []

    lines: List[str] = []
    if os.path.isfile(input_path):
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                content = f.read()

            stripped = content.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                try:
                    urls = json.loads(stripped)
                    if isinstance(urls, list):
                        for i in range(0, len(urls), 1):
                            if isinstance(urls[i], str) and urls[i].strip():
                                lines.append(urls[i].strip())
                except json.JSONDecodeError:
                    print(f"Error: Invalid JSON format in {input_path}")
                    return []
            else:
                lines = [ln.rstrip("\n") for ln in content.splitlines()]
        except Exception as e:
            print(f"Error reading file {input_path}: {e}")
            return []
    else:
        lines = [input_path]

    last_dataset_url: Optional[str] = None

    for line_num, raw_line in enumerate(lines, 1):
        line = (raw_line or "").strip()
        if not line or _line_is_effectively_blank(line):
            continue

        tokens = _URL_TOKEN_RE.findall(line)
        if not tokens:
            parts = [p.strip().strip('"').strip("'") for p in line.split(",")]
            tokens = [p for p in parts if p]

        model_candidates: List[str] = []
        dataset_candidates: List[str] = []
        code_candidates: List[str] = []

        for tok in tokens:
            kind, norm = _classify_and_normalize(tok)
            if kind == "model" and norm not in model_candidates:
                model_candidates.append(norm)
            elif kind == "dataset" and norm not in dataset_candidates:
                dataset_candidates.append(norm)
            elif kind == "code" and norm not in code_candidates:
                code_candidates.append(norm)

        if not model_candidates and "," in line:
            parts = [p.strip().strip('"').strip("'") for p in line.split(",")]
            while len(parts) < 3:
                parts.append("")
            code_url_fb, dataset_url_fb, model_url_fb = parts[0], parts[1], parts[2]
            if is_model_url(model_url_fb):
                model_candidates.append(_normalize_hf_model_url(model_url_fb))
            if is_dataset_url(dataset_url_fb):
                dataset_candidates.append(_normalize_hf_dataset_url(dataset_url_fb))
            if "github.com/" in (code_url_fb or ""):
                code_candidates.append(_normalize_github_repo_url(code_url_fb))

        if not model_candidates:
            continue

        chosen_dataset = dataset_candidates[0] if dataset_candidates else (last_dataset_url or "")
        chosen_code = code_candidates[0] if code_candidates else ""

        if chosen_dataset:
            last_dataset_url = chosen_dataset
            if chosen_dataset not in seen_datasets:
                seen_datasets[chosen_dataset] = {"url": chosen_dataset, "line": line_num}

        for murl in model_candidates:
            parsed_entries.append(
                {
                    "category": "MODEL",
                    "url": murl,
                    "name": extract_model_name(murl),
                    "dataset_url": chosen_dataset or "",
                    "code_url": chosen_code or "",
                }
            )

    return parsed_entries


def extract_model_name(url: str) -> str:
    """Extract model name from HuggingFace URL"""
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
                    print(f"Scraping README for {model_id} to find GitHub URLs...")

                readme_content = fetch_huggingface_readme(model_id)
                if readme_content:
                    github_urls = extract_github_urls_from_text(readme_content)
                    if github_urls:
                        entry["code_url"] = github_urls[0]
                        if debug:
                            print(f"Found GitHub URL in README: {github_urls[0]}")
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
