import sys
import os
import json
from metrics.data_quality import DatasetQualityMetric
from metrics.dataset_and_code import DatasetAndCodeMetric
from utils.parse_input import fetch_metadata
from utils.output_format import format_score_row, print_score_table
from utils.parse_input import parse_input_file
from scorer2 import Scorer 

def process(parsed_data):
    rows = []
    scorer = Scorer()

    ds = DatasetQualityMetric()
    dc = DatasetAndCodeMetric()

    for entry in parsed_data:
        # IF WE DONT WANT TO HANDLE NULL CHECKS IN METRICS
        # category = entry.get("category")
        # if category == "MODEL":
        #     continue
        # elif category == "DATASET":
        #     continue
        # elif category == "CODE":
        #     continue

        metadata = fetch_metadata(entry)
        ds.calculate_score(metadata)
        # dc.calculate_score(metadata)
        row = format_score_row(metadata, scorer)
        rows.append(row)

    print_score_table(rows)

def main():
    if len(sys.argv) != 2:
        print("Usage: python src/__init__.py <URL_FILE or 'dev'>")
        sys.exit(1)

    input_file = sys.argv[1]

    if input_file == "dev":
        INPUT_DIR = "input"
        files = [f for f in os.listdir(INPUT_DIR) if os.path.isfile(os.path.join(INPUT_DIR, f))]
        
        if not files:
            print("No files found in the input directory.")
            sys.exit(1)

        input_file_path = os.path.join(INPUT_DIR, files[1])
        
        try:
            with open(input_file_path, 'r') as file:
                urls = json.load(file)
            
            for url in urls:
                parsed_data = parse_input_file(url)
                process(parsed_data)
        except Exception as e:
            print(f"Error processing file {input_file_path}: {e}")
            sys.exit(1)
            
    else:
        if input_file.startswith("http://") or input_file.startswith("https://"):
            parsed_data = parse_input_file(input_file)
            process_category(parsed_data)
        else:
            print("Error: Invalid input. Please provide a URL or 'dev' for local files.")
            sys.exit(1)

if __name__ == "__main__":
    main()

