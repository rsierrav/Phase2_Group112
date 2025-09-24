# src/cli.py
import os
import sys
import json
from typing import Dict, Any, List
from src.utils.parse_input import parse_input_file, fetch_metadata
from src.utils.output_format import format_score_row
from src.scorer import Scorer
from src.metrics.data_quality import DatasetQualityMetric

INPUT_DIR = "input"


def process_and_score_input_file(input_file: str) -> None:
    """Parse, fetch metadata, score entries, and output results in NDJSON."""

    scorer = Scorer()
    ds = DatasetQualityMetric()

    # Detect .json vs .txt
    try:
        if input_file.endswith(".json"):
            with open(input_file, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    sys.stderr.write(f"Error: invalid JSON in {input_file}\n")
                    sys.exit(1)

            # If file is a list of URLs
            if isinstance(data, list):
                url_lines: List[str] = data
            else:
                sys.stderr.write(f"Error: unsupported JSON format in {input_file}\n")
                sys.exit(1)

        else:  # assume .txt or csv-like
            with open(input_file, "r", encoding="utf-8") as f:
                url_lines = [line.strip() for line in f if line.strip()]
    except Exception as e:
        sys.stderr.write(f"Error reading {input_file}: {e}\n")
        sys.exit(1)

    # Process each URL line
    for raw in url_lines:
        # Handle comma-separated
        urls = [u.strip().strip('"').strip("'") for u in raw.split(",") if u.strip()]
        if not urls:
            continue

        # Only keep model URLs
        for url in urls:
            parsed_entries = parse_input_file(url)
            for entry in parsed_entries:
                if entry.get("category") != "MODEL":
                    continue
                metadata: Dict[str, Any] = fetch_metadata(entry)
                ds.calculate_score(metadata)
                row: Dict[str, Any] = format_score_row(metadata, scorer)

                # Print one JSON object per line (NDJSON)
                print(json.dumps(row))


def run_cli() -> None:
    """Main CLI handler orchestrator."""
    log_level = os.getenv("LOG_LEVEL", "1")

    # Autograder mode: ./run score <file>
    if len(sys.argv) > 2 and sys.argv[1] == "score":
        input_file = sys.argv[2]
        if not os.path.exists(input_file):
            print(f"Error: file not found {input_file}", file=sys.stderr)
            sys.exit(1)
        process_and_score_input_file(input_file)
        return

    # Interactive fallback (local dev mode)
    if not os.path.isdir(INPUT_DIR):
        print(f"Error: input folder '{INPUT_DIR}' not found.")
        sys.exit(1)

    files = [f for f in os.listdir(INPUT_DIR) if os.path.isfile(os.path.join(INPUT_DIR, f))]
    if not files:
        print(f"No files found inside '{INPUT_DIR}'")
        sys.exit(1)

    if log_level != "0":  # hide menus if LOG_LEVEL=0
        print("Available input files:")
        for idx, fname in enumerate(files, start=1):
            print(f"  {idx}. {fname}")

    # Default to first file in autograder (no prompt)
    if not sys.stdin.isatty():
        input_file = os.path.join(INPUT_DIR, files[0])
    else:
        # Local interactive mode
        while True:
            try:
                choice = int(input("Select an input file by number (0 to exit): "))
                if choice == 0:
                    print("Exiting.")
                    sys.exit(0)
                if 1 <= choice <= len(files):
                    input_file = os.path.join(INPUT_DIR, files[choice - 1])
                    break
                else:
                    print("Invalid selection. Please enter a number from the list.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    process_and_score_input_file(input_file)
