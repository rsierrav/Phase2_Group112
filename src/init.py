import sys
import os
import json
from src.metrics.data_quality import DatasetQualityMetric
from src.utils.parse_input import fetch_metadata
from src.utils.output_format import format_score_row
from src.utils.parse_input import parse_input_file
from src.scorer import Scorer


def process(parsed_data):
    scorer = Scorer()
    ds = DatasetQualityMetric()

    for entry in parsed_data:
        metadata = fetch_metadata(entry)
        ds.calculate_score(metadata)
        row = format_score_row(metadata, scorer)
        print(json.dumps(row))


def clean_and_split_line(line: str):
    """
    Split a line by commas, strip whitespace/quotes/brackets,
    and drop empty tokens.
    """
    tokens = []
    for part in line.split(","):
        cleaned = part.strip().strip('"').strip("'").strip("[]").strip()
        if cleaned:
            tokens.append(cleaned)
    return tokens


def main():
    if len(sys.argv) != 2:
        print("Usage: python src/init.py <URL | 'dev'>")
        sys.exit(1)

    input_file = sys.argv[1]

    if input_file == "dev":
        INPUT_DIR = "input"
        files = [f for f in os.listdir(INPUT_DIR) if os.path.isfile(os.path.join(INPUT_DIR, f))]

        if not files:
            print("No files found in the input directory.")
            sys.exit(1)

        input_file_path = os.path.join(INPUT_DIR, files[0])

        try:
            with open(input_file_path, "r") as file:
                for line in file:
                    urls = clean_and_split_line(line)
                    for url in urls:
                        parsed_data = parse_input_file(url)
                        process(parsed_data)
        except Exception as e:
            print(f"Error processing file {input_file_path}: {e}")
            sys.exit(1)

    else:
        if input_file.startswith("http://") or input_file.startswith("https://"):
            parsed_data = parse_input_file(input_file)
            process(parsed_data)
        else:
            print("Error: Invalid input. Please provide a URL or 'dev' for local files.")
            sys.exit(1)


if __name__ == "__main__":
    main()
