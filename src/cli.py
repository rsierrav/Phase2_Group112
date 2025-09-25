# src/cli.py
import os
import sys
import json
import logging
import requests
from typing import Dict, Any
from src.utils.parse_input import parse_input_file, fetch_metadata
from src.utils.output_format import format_score_row
from src.scorer import Scorer

INPUT_DIR = "input"


def validate_github_token() -> None:
    token = os.getenv("GITHUB_TOKEN")
    if not token or not token.strip():
        sys.stderr.write("Error: GITHUB_TOKEN not set or empty\n")
        sys.exit(1)

    headers = {"Authorization": f"token {token}"}
    try:
        resp = requests.get("https://api.github.com/rate_limit", headers=headers, timeout=5)
        if resp.status_code != 200:
            sys.stderr.write("Error: Invalid GITHUB_TOKEN\n")
            sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Error: GitHub token validation failed ({e})\n")
        sys.exit(1)


def validate_log_file() -> None:
    log_path = os.getenv("LOG_FILE")
    if not log_path:
        sys.stderr.write("Error: LOG_FILE not set\n")
        sys.exit(1)

    parent = os.path.dirname(log_path) or "."
    if not os.path.isdir(parent):
        sys.stderr.write(f"Error: parent directory {parent} does not exist\n")
        sys.exit(1)

    if os.path.exists(log_path):
        if not os.access(log_path, os.W_OK):
            sys.stderr.write(f"Error: cannot write to log file {log_path}\n")
            sys.exit(1)
    else:
        # Do not create new file (per Piazza)
        sys.stderr.write(f"Error: log file {log_path} does not exist\n")
        sys.exit(1)

    # Handle log level
    level_str = os.getenv("LOG_LEVEL", "1")
    if level_str == "0":
        logging.disable(logging.CRITICAL)
        return
    elif level_str == "2":
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(
        filename=log_path,
        level=log_level,
        format="%(asctime)s %(levelname)s: %(message)s",
    )
    logging.info("Logging initialized successfully.")


def process_and_score_input_file(input_file: str) -> None:
    """Parse, fetch metadata, score entries, and output results in NDJSON."""

    scorer = Scorer()
    parsed_entries = parse_input_file(input_file)

    for entry in parsed_entries:
        if entry.get("category") != "MODEL":
            continue
        metadata: Dict[str, Any] = fetch_metadata(entry)
        row: Dict[str, Any] = format_score_row(metadata, scorer)
        print(json.dumps(row))


def run_cli() -> None:
    """Main CLI handler orchestrator."""
    # Validate env vars first
    validate_github_token()
    validate_log_file()

    # Autograder mode: ./run score <file>
    if len(sys.argv) > 2 and sys.argv[1] == "score":
        input_file = sys.argv[2]
        if not os.path.exists(input_file):
            print(f"Error: file not found {input_file}", file=sys.stderr)
            sys.exit(1)
        process_and_score_input_file(input_file)
        return

    if not os.path.isdir(INPUT_DIR):
        print(f"Error: input folder '{INPUT_DIR}' not found.", file=sys.stderr)
        sys.exit(1)

    files = [f for f in os.listdir(INPUT_DIR) if os.path.isfile(os.path.join(INPUT_DIR, f))]
    if not files:
        print(f"No files found inside '{INPUT_DIR}'", file=sys.stderr)
        sys.exit(1)

    process_and_score_input_file(os.path.join(INPUT_DIR, files[0]))
