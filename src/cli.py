# cli.py
import os
import sys
from typing import List, Dict, Any
from src.utils.parse_input import parse_input_file, fetch_metadata
# from src.scorer import score

INPUT_DIR = "input"
OUTPUT_DIR = "output"  # NDJSON output folder


def get_available_input_files() -> List[str]:
    """Return a list of files in INPUT_DIR, exit if folder or files are missing."""
    if not os.path.isdir(INPUT_DIR):
        print(f"Error: input folder '{INPUT_DIR}' not found.")
        sys.exit(1)

    files = [f for f in os.listdir(INPUT_DIR) if os.path.isfile(os.path.join(INPUT_DIR, f))]
    if not files:
        print(f"No files found inside '{INPUT_DIR}'")
        sys.exit(1)

    print("Available input files:")
    for idx, fname in enumerate(files, start=1):
        print(f"  {idx}. {fname}")

    return files


def prompt_user_for_file_selection(files: List[str]) -> str:
    """Prompt user to select an input file by number."""
    while True:
        try:
            choice = int(input("Select an input file by number (0 to exit): "))
            if choice == 0:
                print("Exiting.")
                sys.exit(0)
            if 1 <= choice <= len(files):
                return os.path.join(INPUT_DIR, files[choice - 1])
            else:
                print("Invalid selection. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def process_and_score_input_file(input_file: str) -> None:
    """Parse, fetch metadata, score entries, and output results."""
    print(f"\nUsing input file: {input_file}\n")

    # Parse input URLs
    entries: List[Dict[str, Any]] = parse_input_file(input_file)

    # Fetch metadata for each entry
    for entry in entries:
        fetch_metadata(entry)

    # Score each entry
    # results: List[Dict[str, Any]] = [score(entry) for entry in entries]

    # Output results
    # output_formate.function()


def run_cli() -> None:
    """Main CLI handler orchestrator."""
    files = get_available_input_files()
    input_file = prompt_user_for_file_selection(files)
    process_and_score_input_file(input_file)
