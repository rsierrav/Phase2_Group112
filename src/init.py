# src/init.py

import sys
import os
import json

# Fix import issues when running from root directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402
from src.utils.parse_input import fetch_metadata, parse_input_file  # noqa: E402
from src.utils.output_format import format_score_row  # noqa: E402
from src.scorer import Scorer  # noqa: E402


def process(parsed_data):
    """Process parsed entries, but only output MODEL category rows."""
    if not parsed_data:
        return
    scorer = Scorer()

    for entry in parsed_data:
        if entry.get("category") != "MODEL":
            continue
        metadata = fetch_metadata(entry)
        row = format_score_row(metadata, scorer)
        # Strict NDJSON: one JSON object per line, no spaces
        print(json.dumps(row, separators=(",", ":")))


def clean_and_split_line(line: str):
    """Split a line by commas, strip whitespace/quotes/brackets, and drop empty tokens."""
    tokens = []
    for part in line.split(","):
        cleaned = part.strip().strip('"').strip("'").strip("[]").strip()
        if cleaned:
            tokens.append(cleaned)
    return tokens


def process_file_lines(file_path: str):
    """Read a file and process its URLs (handles both .txt and .json)."""
    try:
        if file_path.endswith(".json"):
            with open(file_path, "r", encoding="utf-8") as file:
                try:
                    urls = json.load(file)
                except json.JSONDecodeError as e:
                    sys.stderr.write(f"Error parsing JSON file {file_path}: {e}\n")
                    sys.exit(1)

            if not isinstance(urls, list):
                sys.stderr.write(f"Error: JSON file {file_path} must contain a list of URLs\n")
                sys.exit(1)

            url_line = ",".join([u for u in urls if isinstance(u, str) and u.strip()])
            if url_line:
                parsed_data = parse_input_file(url_line)
                if parsed_data:
                    process(parsed_data)

        else:
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    urls = clean_and_split_line(line)
                    if not urls:
                        continue
                    # ✅ Pass all URLs on this line together
                    url_line = ",".join(urls)
                    parsed_data = parse_input_file(url_line)
                    if parsed_data:
                        process(parsed_data)

    except Exception as e:
        sys.stderr.write(f"Error processing file {file_path}: {e}\n")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python src/init.py <URL | URL_FILE | 'dev'>\n")
        sys.exit(1)

    if sys.argv[1] == "score" and len(sys.argv) >= 3:
        input_file = sys.argv[2]
    else:
        input_file = sys.argv[1]

    if input_file == "dev":
        input_dir = "input"
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        if not files:
            sys.stderr.write("No files found in the input directory.\n")
            sys.exit(1)
        input_file_path = os.path.join(input_dir, files[0])
        process_file_lines(input_file_path)

    elif input_file.startswith("http://") or input_file.startswith("https://"):
        parsed_data = parse_input_file(input_file)
        if parsed_data:
            process(parsed_data)

    elif os.path.isfile(input_file):
        process_file_lines(input_file)

    elif os.path.isfile(os.path.join("input", input_file)):
        process_file_lines(os.path.join("input", input_file))

    else:
        sys.stderr.write("Error: Invalid input. Please provide a URL, a file, or 'dev'.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
