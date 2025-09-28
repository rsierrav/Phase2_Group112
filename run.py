#!/usr/bin/env python3
import sys
import subprocess
import os

# Trying to fix import issues when running from root directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.cli import run_cli, process_and_score_input_file  # noqa: E402

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
    try:
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
coverage==7.3.2
"""
                )
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS])
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] pip failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected install error: {e}")
        sys.exit(1)


def run_tests():
    """Run the test suite and report results in spec format."""
    tests_dir = os.path.join(SCRIPT_DIR, "tests")

    if not os.path.isdir(tests_dir):
        print("Error: No tests directory found")
        sys.exit(1)

    try:
        # Simple pytest run
        result = subprocess.run([sys.executable, "-m", "pytest", tests_dir, "-v"], capture_output=True, text=True)

        # Print the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        # Exit with pytest's return code
        sys.exit(result.returncode)

    except FileNotFoundError:
        # Fallback if pytest not available - use unittest
        try:
            result = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", tests_dir, "-v"],
                capture_output=True,
                text=True,
            )
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            sys.exit(result.returncode)
        except Exception as e:
            print(f"Error running tests: {e}")
            sys.exit(1)


def process_urls_with_cli(url_file: str):
    if not os.path.exists(url_file):
        print(f"Error: input file '{url_file}' not found")
        sys.exit(1)
    process_and_score_input_file(url_file)


def process_local_files():
    if not os.path.exists(MAIN_SCRIPT):
        print("Error: init.py not found")
        sys.exit(1)
    subprocess.check_call([sys.executable, "-m", "src.init", "dev"], cwd=SCRIPT_DIR)


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
    elif command.startswith("/") or os.path.exists(command):
        # Handle file path directly
        process_urls_with_cli(command)
    else:
        # Default case - shouldn't happen in normal autograder usage
        print(f"DEBUG: Falling through to run_cli() with command: {command}", file=sys.stderr)
        run_cli()
