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


# Run tests and output according to spec
def run_tests():
    tests_dir = os.path.join(SCRIPT_DIR, "tests")

    if not os.path.isdir(tests_dir):
        print("Error: No test suite found")
        sys.exit(1)

    try:
        # Run pytest with coverage
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                tests_dir,
                "--maxfail=1",
                "--disable-warnings",
                "-q",
                "--tb=short",
                "--cov=src",
                "--cov-report=term",
            ],
            capture_output=True,
            text=True,
        )

        # Extract number of tests run and passed
        stdout = result.stdout.splitlines()
        summary_line = next((line for line in stdout if "passed" in line or "failed" in line), "")

        passed = failed = total = 0
        if "passed" in summary_line or "failed" in summary_line:
            parts = summary_line.split(",")
            for part in parts:
                part = part.strip()
                if part.endswith("passed"):
                    passed = int(part.split()[0])
                elif part.endswith("failed"):
                    failed = int(part.split()[0])
            total = passed + failed

        # Get coverage % using coverage report
        cov_result = subprocess.run(
            [sys.executable, "-m", "coverage", "report"], capture_output=True, text=True
        )
        cov_lines = cov_result.stdout.splitlines()
        coverage_percent = 0
        if cov_lines:
            last_line = cov_lines[-1]
            if "%" in last_line:
                try:
                    coverage_percent = int(last_line.strip().split()[-1].replace("%", ""))
                except Exception:
                    coverage_percent = 0

        # Print in required format
        print(f"{passed}/{total} test cases passed. {coverage_percent}% line coverage achieved.")

        # Exit code: 0 if all passed and coverage >= 80%
        if failed == 0 and coverage_percent >= 80:
            sys.exit(0)
        else:
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"Tests failed with exit code {e.returncode}")
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
    elif command == "score":
        if len(sys.argv) < 3:
            print("Error: Missing URL_FILE argument for score command")
            sys.exit(1)
        process_urls_with_cli(sys.argv[2])
    else:
        run_cli()
