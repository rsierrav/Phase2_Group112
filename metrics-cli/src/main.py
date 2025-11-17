import sys
import os
import json
import logging

# Fix import issues when running from root directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402
from src.utils.parse_input import fetch_metadata, parse_input_file  # noqa: E402
from src.utils.output_format import format_score_row  # noqa: E402
from src.scorer import Scorer  # noqa: E402


def process(parsed_data):
    """Process parsed entries, but only output MODEL category rows."""
    if not parsed_data:
        logging.warning("No parsed data provided to process()")
        return

    logging.info(f"Processing {len(parsed_data)} entries")
    scorer = Scorer()

    for entry in parsed_data:
        logging.debug(
            f"Processing entry: {entry.get('url', '')} (category={entry.get('category')})"
        )
        if entry.get("category") != "MODEL":
            logging.info(f"Skipping non-MODEL entry: {entry.get('url', '')}")
            continue
        try:
            metadata = fetch_metadata(entry)
            logging.debug(f"Fetched metadata for {entry.get('url', '')}")
            row = format_score_row(metadata, scorer)
            print(json.dumps(row, separators=(",", ":")))
            logging.info(f"Scored model entry: {row.get('name', 'unknown')}")
        except Exception as e:
            logging.error(f"Error processing entry {entry.get('url', '')}: {e}", exc_info=True)


def main():
    logging.debug("Entered main()")
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python src/init.py <URL | URL_FILE | 'dev'>\n")
        logging.error("Invalid usage: no argument provided")
        sys.exit(1)

    input_file = None
    if sys.argv[1] == "score" and len(sys.argv) >= 3:
        input_file = sys.argv[2]
    else:
        input_file = sys.argv[1]

    if input_file == "dev":
        input_dir = "input"
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        if not files:
            sys.stderr.write("No files found in the input directory.\n")
            logging.error("Dev mode: no files in input directory")
            sys.exit(1)
        logging.info(f"Dev mode: processing {files[0]}")
        input_file_path = os.path.join(input_dir, files[0])
        parsed_data = parse_input_file(input_file_path)
        if parsed_data:
            process(parsed_data)

    elif input_file.startswith("http://") or input_file.startswith("https://"):
        logging.info(f"Processing direct URL input: {input_file}")
        parsed_data = parse_input_file(input_file)
        if parsed_data:
            process(parsed_data)

    elif os.path.isfile(input_file):
        logging.info(f"Processing local file: {input_file}")
        parsed_data = parse_input_file(input_file)
        if parsed_data:
            process(parsed_data)

    elif os.path.isfile(os.path.join("input", input_file)):
        input_file_path = os.path.join("input", input_file)
        logging.info(f"Processing file from input folder: {input_file_path}")
        parsed_data = parse_input_file(input_file_path)
        if parsed_data:
            process(parsed_data)

    else:
        sys.stderr.write("Error: Invalid input. Please provide a URL, a file, or 'dev'.\n")
        logging.error(f"Invalid input argument: {input_file}")
        sys.exit(1)


if __name__ == "__main__":
    main()
