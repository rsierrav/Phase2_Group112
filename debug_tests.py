#!/usr/bin/env python3
"""
Debug script to understand what's happening with your test suite
"""
import os
import sys
import subprocess


def check_test_setup():
    """Check if test environment is set up correctly"""
    print("=== CHECKING TEST SETUP ===")
    print()

    # Check if tests directory exists
    if os.path.exists("tests"):
        print("✅ tests/ directory exists")
        test_files = [f for f in os.listdir("tests") if f.startswith("test_") and f.endswith(".py")]
        print(f"   Found {len(test_files)} test files:")
        for f in test_files:
            print(f"   - {f}")
    else:
        print("❌ tests/ directory not found")
        return False


def run_pytest_directly():
    """Run pytest directly to see what happens"""
    print("\n=== RUNNING PYTEST DIRECTLY ===")
    print()

    print("Command: pytest tests/ -v")
    try:
        result = subprocess.run(["python", "-m", "pytest", "tests/", "-v"], capture_output=True, text=True, timeout=30)

        print(f"Return code: {result.returncode}")
        print("\nSTDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)

    except subprocess.TimeoutExpired:
        print("❌ Pytest timed out after 30 seconds")
    except Exception as e:
        print(f"❌ Error running pytest: {e}")


def test_imports():
    """Test if your source modules can be imported"""
    print("\n=== TESTING IMPORTS ===")
    print()

    modules_to_test = [
        "src.scorer",
        "src.utils.parse_input",
        "src.utils.output_format",
        "src.metrics.dataset_and_code",
        "src.metrics.license",
        "src.metrics.size",
    ]

    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
        except Exception as e:
            print(f"⚠️  {module}: {e}")


def run_coverage_directly():
    """Run coverage directly to see output"""
    print("\n=== RUNNING COVERAGE DIRECTLY ===")
    print()

    print("Command: pytest tests/ --cov=src --cov-report=term")
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "--cov=src", "--cov-report=term"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        print(f"Return code: {result.returncode}")
        print("\nSTDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)

    except subprocess.TimeoutExpired:
        print("❌ Coverage pytest timed out after 30 seconds")
    except Exception as e:
        print(f"❌ Error running coverage: {e}")


def simulate_run_test():
    """Simulate what your run_test() function does"""
    print("\n=== SIMULATING RUN_TEST() FUNCTION ===")
    print()

    import pytest
    import re
    import io
    from contextlib import redirect_stdout, redirect_stderr

    # Capture pytest output just like your function does
    buffer = io.StringIO()
    with redirect_stdout(buffer), redirect_stderr(buffer):
        result = pytest.main(["tests/", "--cov=src", "--cov-report=term-missing"])

    output = buffer.getvalue()

    print(f"Pytest return code: {result}")
    print(f"Captured output length: {len(output)} characters")
    print("\nRaw captured output:")
    print("=" * 50)
    print(output)
    print("=" * 50)

    # Parse like your function does
    total_tests = 0
    m = re.search(r"collected (\d+) items?", output)
    if m:
        total_tests = int(m.group(1))
        print(f"\n✅ Found total tests: {total_tests}")
    else:
        print("\n❌ Could not find 'collected N items' pattern")

    passed_tests = 0
    m = re.search(r"(\d+) passed", output)
    if m:
        passed_tests = int(m.group(1))
        print(f"✅ Found passed tests: {passed_tests}")
    else:
        print("❌ Could not find 'N passed' pattern")

    coverage_percent = 0
    m = re.search(r"^TOTAL.*?(\d+)%", output, re.MULTILINE)
    if m:
        coverage_percent = int(m.group(1))
        print(f"✅ Found coverage: {coverage_percent}%")
    else:
        print("❌ Could not find 'TOTAL ... N%' pattern")

    print(f"\nFinal result: {passed_tests}/{total_tests} test cases passed. {coverage_percent}% line coverage achieved.")


if __name__ == "__main__":
    print("DEBUGGING YOUR TEST SUITE")
    print("=" * 50)

    # Add current directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    if check_test_setup():
        test_imports()
        run_pytest_directly()
        run_coverage_directly()
        simulate_run_test()
    else:
        print("\n❌ Basic test setup is incomplete. Fix the issues above first.")
