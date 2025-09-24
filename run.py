#!/usr/bin/env python3
import sys
import subprocess
import os
import json
from src.cli import run_cli

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(SCRIPT_DIR, "src", "init.py")
REQUIREMENTS = os.path.join(SCRIPT_DIR, "requirements.txt")


def show_usage():
    print("Usage:")
    print("  ./run install               - Install dependencies")
    print("  ./run score <URL_FILE>      - Score models from a file")
    print("  ./run dev                   - Run all input files (dev mode)")
    print("  ./run test                  - Run test suite")
    sys.exit(1)


def install_dependencies():
    print("Installing dependencies...")

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
    print("Dependencies installed successfully")


def run_tests():
    test_suite = os.path.join(SCRIPT_DIR, "test_suite.py")
    tests_dir = os.path.join(SCRIPT_DIR, "tests")

    if os.path.exists(test_suite):
        subprocess.check_call([sys.executable, test_suite])
    elif os.path.isdir(tests_dir):
        subprocess.check_call([sys.executable, "-m", "pytest", tests_dir, "-v"])
    else:
        sys.exit("Error: No test suite found")


def process_and_stream(command: list):
    """
    Run a subprocess (init.py) and stream its stdout line by line.
    Converts any JSON arrays into NDJSON (one object per line).
    """
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Collect stdout, parse if needed
    if proc.stdout is None:
        return

    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            # If it's a list, break into objects
            if isinstance(data, list):
                for obj in data:
                    print(json.dumps(obj))
            elif isinstance(data, dict):
                print(json.dumps(data))
            else:
                # Already NDJSON-safe
                print(json.dumps({"output": data}))
        except Exception:
            # Just print raw if it's not JSON
            print(line)

    proc.wait()
    if proc.returncode != 0:
        sys.exit(proc.returncode)


def process_urls(url_file: str):
    if not os.path.exists(MAIN_SCRIPT):
        print("Error: init.py not found")
        sys.exit(1)
    process_and_stream([sys.executable, MAIN_SCRIPT, url_file])


def process_local_files():
    if not os.path.exists(MAIN_SCRIPT):
        print("Error: init.py not found")
        sys.exit(1)
    process_and_stream([sys.executable, MAIN_SCRIPT, "dev"])


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
        process_urls(sys.argv[2])
    else:
        # fallback to run_cli (custom CLI handler)
        run_cli()
