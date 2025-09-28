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


def run_test():
    """Run the test suite and report results in spec format."""
    import pytest
    import sys
    import re
    import io
    from contextlib import redirect_stdout, redirect_stderr

    # Capture pytest output (quiet + coverage)
    buffer = io.StringIO()
    with redirect_stdout(buffer), redirect_stderr(buffer):
        result = pytest.main(["tests/", "-q", "--tb=no", "--cov=src", "--cov-report=term"])

    output = buffer.getvalue()

    # --- Parse test results ---
    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    for line in output.splitlines():
        # Examples: "140 passed in 2.34s" or "2 failed, 140 passed in 8.87s"
        if "failed" in line and "passed" in line:
            m = re.search(r"(\d+) failed.*?(\d+) passed", line)
            if m:
                failed_tests = int(m.group(1))
                passed_tests = int(m.group(2))
                total_tests = failed_tests + passed_tests
                break
        elif "passed" in line and "failed" not in line:
            m = re.search(r"(\d+) passed", line)
            if m:
                passed_tests = total_tests = int(m.group(1))
                failed_tests = 0
                break

    # --- Parse coverage ---
    coverage_percent = 0
    for line in output.splitlines():
        # pytest-cov prints like: "TOTAL ... 59%"
        m = re.search(r"TOTAL.*?(\d+)%", line)
        if m:
            coverage_percent = int(m.group(1))
            break

    # --- Final output in exact required format ---
    print(f"{passed_tests}/{total_tests} test cases passed. {coverage_percent}% line coverage achieved.")

    sys.exit(result)


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
        run_test()
    elif command == "score":
        if len(sys.argv) < 3:
            print("Error: Missing URL_FILE argument for score command")
            sys.exit(1)
        process_urls_with_cli(sys.argv[2])
    else:
        run_cli()
