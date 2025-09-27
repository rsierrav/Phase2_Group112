# debug_parser.py - Run this to see what parse_input.py produces

import sys
import os

# Fix import issues when running from root directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import the fixed version first, fall back to old version
try:
    from src.utils.parse_input import fetch_metadata, parse_input_file

    print("INFO: Using updated parse_input.py (if you replaced the file)")
except ImportError:
    print("ERROR: Could not import from src.utils.parse_input")
    sys.exit(1)


def debug_parse_input_file():
    """Debug version that shows what parse_input.py produces"""

    # Use the same input file that 'run dev' would use
    input_dir = "input"
    files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]

    if not files:
        print("No files found in the input directory.")
        return

    # Process all files in input directory
    for filename in files:
        input_file_path = os.path.join(input_dir, filename)
        print(f"Reading from: {input_file_path}")
        print("=" * 60)
        debug_single_file(input_file_path)
        print("\n" + "END OF FILE" + "=" * 50 + "\n")


def debug_single_file(input_file_path: str):

    # Read the file content
    with open(input_file_path, "r", encoding="utf-8") as file:
        content = file.read()
        print("RAW FILE CONTENT:")
        print(repr(content))  # shows whitespace and special chars
        print("\n" + "=" * 60)

    # Use the FIXED parse_input_file function
    print("USING FIXED PARSER...")
    parsed_entries = parse_input_file(input_file_path)

    if parsed_entries:
        print(f"Found {len(parsed_entries)} MODEL entries:")

        for i, entry in enumerate(parsed_entries, 1):
            print(f"\nMODEL ENTRY {i}:")
            print(f"    Name: {entry.get('name')}")
            print(f"    URL: {entry.get('url')}")
            print(f"    Code URL: {entry.get('code_url') or 'None'}")
            print(f"    Dataset URL: {entry.get('dataset_url') or 'None'}")

            # Fetch full metadata
            print(f"\nFETCHING METADATA for {entry['name']}...")
            metadata = fetch_metadata(entry, debug=True)

            print("\nFINAL RESULT:")
            print(f"    Model Size: {metadata.get('model_size_mb', 0)} MB")
            print(f"    License: {metadata.get('license', 'Not found')}")
            print(f"    Downloads: {metadata.get('downloads', 0)}")
            print(f"    Likes: {metadata.get('likes', 0)}")

            # Code quality check
            print("\nCODE QUALITY CHECK:")
            if metadata.get("code_url"):
                if "github.com" in metadata["code_url"]:
                    print(f"    [SUCCESS] GitHub repo found: {metadata['code_url']}")
                    print("    Code quality metric CAN analyze this!")
                else:
                    print(f"    [WARNING] Non-GitHub code URL: {metadata['code_url']}")
                    print("    Code quality will score 0 (not a GitHub repo)")
            else:
                print("    [ERROR] No code URL found")
                print("    Code quality will score 0")

            # Dataset check
            print("\nDATASET CHECK:")
            if metadata.get("dataset_url"):
                print(f"    [SUCCESS] Dataset URL found: {metadata['dataset_url']}")
                print("    Dataset metrics CAN use this!")
            else:
                print("    [ERROR] No dataset URL found")
                print("    Dataset-related metrics may score lower")

            print("\n" + "-" * 60)
    else:
        print("[ERROR] No MODEL entries found!")

    # Show global dataset registry
    from src.utils.parse_input import seen_datasets

    if seen_datasets:
        print(f"\nGLOBAL DATASET REGISTRY ({len(seen_datasets)} datasets):")
        for url in seen_datasets:
            print(f"    * {url}")
    else:
        print("\nGLOBAL DATASET REGISTRY: Empty")


if __name__ == "__main__":
    debug_parse_input_file()
