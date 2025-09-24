import os
import sys
import json
from typing import Dict, Any, List
from src.utils.parse_input import parse_input_file, fetch_metadata
from src.scorer import Scorer

INPUT_DIR = "input"
OUTPUT_DIR = "output"

def process_and_score_input_file(input_file: str) -> None:
    """Parse, fetch metadata, score entries, and output results in NDJSON."""
    scorer = Scorer()
    
    # Use the existing parse_input_file function to handle URL parsing and categorization
    try:
        entries = parse_input_file(input_file)
        
        if not entries:
            print(f"Warning: No valid entries found in {input_file}", file=sys.stderr)
            return
            
        for entry in entries:
            # Fetch metadata for each entry
            entry_with_metadata = fetch_metadata(entry)
            
            # Score the complete entry
            result = scorer.score(entry_with_metadata)
            
            # Always output result
            if result is not None:
                print(json.dumps(result))
            
    except Exception as e:
        print(f"Error processing file {input_file}: {e}", file=sys.stderr)
        sys.exit(1)

def run_cli() -> None:
    """Main CLI handler orchestrator."""
    log_level = os.getenv("LOG_LEVEL", "1")
    
    # If an argument is passed, use it directly (for autograder)
    if len(sys.argv) > 2 and sys.argv[1] == "score":
        input_file = sys.argv[2]
        if not os.path.exists(input_file):
            print(f"Error: file not found {input_file}", file=sys.stderr)
            sys.exit(1)
        process_and_score_input_file(input_file)
        return
    
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
