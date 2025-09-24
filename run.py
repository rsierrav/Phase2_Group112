#!/usr/bin/env python3
import sys
import subprocess
import os
from src.cli import run_cli, process_and_score_input_file

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(SCRIPT_DIR, "src", "init.py")
REQUIREMENTS = os.path.join(SCRIPT_DIR, "requirements.txt")


def show_usage():
    print("Usage:")
    print("  ./run install               - Install dependencies")
    print("  ./run score <URL_FILE>      - Score models from a file (NDJSON output)")
    print("  ./run dev                   - Run all input files (dev mode)")
    print("  ./run test                  - Run test suite")
    sys.exit(1)


def install_dependencies():
    if not os.path.exists(REQUIREMENTS):
        with open(REQUIREMENTS, "w") as f:
            f.write(
                """requests>=2.25.0
beautifulsoup4>=4.9.0
lxml>=4.6.0
python-dateutil>=2.8.0
urllib3>=1.26.0
GitPython>=3.1.0
PyGithub>=1.55.0
huggingface-hub>=0.10.0
flake8==7.0.0
black==24.8.0
pre-commit==3.6.2
pytest==8.3.2
"""
            )

    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS])


def run_tests():
    test_suite = os.path.join(SCRIPT_DIR, "test_suite.py")
    tests_dir = os.path.join(SCRIPT_DIR, "tests")

    if os.path.exists(test_suite):
        subprocess.check_call([sys.executable, test_suite])
    elif os.path.isdir(tests_dir):
        subprocess.check_call([sys.executable, "-m", "pytest", tests_dir, "-v"])
    else:
        sys.exit("Error: No test suite found")


def process_urls_with_cli(url_file: str):
    """Use the CLI pipeline for scoring (autograder safe)."""
    if not os.path.exists(url_file):
        print(f"Error: input file '{url_file}' not found")
        sys.exit(1)
    process_and_score_input_file(url_file)


def process_local_files():
    """Keep dev mode pointing to init.py for now (prints tables)."""
    if not os.path.exists(MAIN_SCRIPT):
        print("Error: init.py not found")
        sys.exit(1)
    subprocess.check_call([sys.executable, MAIN_SCRIPT, "dev"])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_usage()

    command = sys.argv[1]

    if command == "install":
        install_dependencies()
    elif command == "test":
        run_tests()
    elif command == "dev":
        process_local_files()
    elif command == "score":
        if len(sys.argv) < 3:
            print("Error: Missing URL_FILE argument for score command")
            sys.exit(1)
        process_urls_with_cli(sys.argv[2])
    else:
        # fallback to run_cli (interactive/local use)
        run_cli()
