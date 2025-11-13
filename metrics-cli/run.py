#!/usr/bin/env python3
import sys
import subprocess
import os
import logging
import requests

# Trying to fix import issues when running from root directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.cli import run_cli, process_and_score_input_file  # noqa: E402

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(SCRIPT_DIR, "src", "init.py")
REQUIREMENTS = os.path.join(SCRIPT_DIR, "requirements.txt")


def validate_github_token() -> None:
    token = os.getenv("GITHUB_TOKEN")
    if not token or not token.strip():
        sys.stderr.write("Error: Invalid GITHUB_TOKEN\n")
        sys.exit(1)

    headers = {"Authorization": f"token {token}"}
    try:
        resp = requests.get("https://api.github.com/rate_limit", headers=headers, timeout=5)
        if resp.status_code != 200:
            sys.stderr.write("Error: Invalid GITHUB_TOKEN\n")
            sys.exit(1)
    except Exception:
        sys.stderr.write("Error: Invalid GITHUB_TOKEN\n")
        sys.exit(1)


def validate_log_file() -> None:
    log_path = os.getenv("LOG_FILE")
    if not log_path:
        sys.stderr.write("Error: LOG_FILE not set\n")
        sys.exit(1)

    parent = os.path.dirname(log_path) or "."
    if not os.path.isdir(parent):
        sys.stderr.write(f"Error: parent directory {parent} does not exist\n")
        sys.exit(1)

    if os.path.exists(log_path):
        if not os.access(log_path, os.W_OK):
            sys.stderr.write(f"Error: cannot write to log file {log_path}\n")
            sys.exit(1)
    else:
        sys.stderr.write(f"Error: log file {log_path} does not exist\n")
        sys.exit(1)

    level_str = os.getenv("LOG_LEVEL", "1")
    if level_str == "0":
        logging.disable(logging.CRITICAL)
        return
    elif level_str == "2":
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(
        filename=log_path,
        level=log_level,
        format="%(asctime)s %(levelname)s: %(message)s",
    )
    logging.info("Logging initialized successfully.")


def show_usage():
    print("Usage:")
    print("  ./run install               - Install dependencies")
    print("  ./run score <URL_FILE>      - Score models from a file (NDJSON output)")
    print("  ./run dev                   - Run all input files (dev mode)")
    print("  ./run test                  - Run test suite")
    sys.exit(1)


def install_dependencies():
    try:
        logging.info("Installing dependencies...")
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
        logging.info("Dependencies installed successfully.")
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        logging.error(f"Pip failed: {e}")
        print(f"[ERROR] pip failed: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected install error: {e}")
        print(f"[ERROR] Unexpected install error: {e}")
        sys.exit(1)


def run_tests():
    """Run the test suite and report results in spec format."""
    import re
    import io
    from contextlib import redirect_stdout, redirect_stderr

    tests_dir = os.path.join(SCRIPT_DIR, "tests")

    if not os.path.isdir(tests_dir):
        print("Error: No tests directory found")
        sys.exit(1)

    buffer = io.StringIO()
    try:
        logging.info("Running pytest with coverage...")
        with redirect_stdout(buffer), redirect_stderr(buffer):
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    tests_dir,
                    "--cov=src",
                    "--cov-report=term-missing",
                    "-v",
                ],
                capture_output=True,
                text=True,
                cwd=SCRIPT_DIR,
            )

        output = result.stdout + result.stderr

        total_tests = 0
        m = re.search(r"collected (\d+) items?", output)
        if m:
            total_tests = int(m.group(1))

        passed_tests = 0
        m = re.search(r"(\d+) passed", output)
        if m:
            passed_tests = int(m.group(1))

        coverage_percent = 0
        m = re.search(r"^TOTAL.*?(\d+)%", output, re.MULTILINE)
        if m:
            coverage_percent = int(m.group(1))

        logging.info(
            f"Tests complete: {passed_tests}/{total_tests} passed, coverage={coverage_percent}%"
        )
        print(
            f"{passed_tests}/{total_tests} test cases passed. {coverage_percent}% line coverage achieved."
        )

        sys.exit(result.returncode)

    except Exception as e:
        logging.error(f"Error running tests: {e}", exc_info=True)
        print(f"Error running tests: {e}")
        sys.exit(1)


def process_urls_with_cli(url_file: str):
    if not os.path.exists(url_file):
        logging.error(f"Input file not found: {url_file}")
        print(f"Error: input file '{url_file}' not found")
        sys.exit(1)
    logging.info(f"Processing URL file: {url_file}")
    process_and_score_input_file(url_file)


def process_local_files():
    if not os.path.exists(MAIN_SCRIPT):
        logging.error("src/init.py not found")
        print("Error: init.py not found")
        sys.exit(1)
    logging.info("Running dev mode via src/init.py")
    subprocess.check_call([sys.executable, "-m", "src.init", "dev"], cwd=SCRIPT_DIR)


def main():
    """Entry point for the metrics-cli command."""
    if len(sys.argv) < 2:
        show_usage()

    command = sys.argv[1]

    if command != "install":
        validate_github_token()
        validate_log_file()

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
        process_urls_with_cli(command)
    else:
        logging.warning(f"Unknown command {command}, defaulting to run_cli()")
        print(f"DEBUG: Falling through to run_cli() with command: {command}", file=sys.stderr)
        run_cli()


if __name__ == "__main__":
    main()
