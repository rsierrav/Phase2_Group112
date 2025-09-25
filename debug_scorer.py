#!/usr/bin/env python3
"""
Debug the scorer to see what data is being passed to metrics
"""

import sys
import os

# Fix import issues when running from root directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.utils.parse_input import parse_input_file, fetch_metadata  # noqa: E402
from src.metrics.code_quality import code_quality  # noqa: E402
from src.scorer import Scorer  # noqa: E402


def debug_scoring():
    """Debug what data gets passed to the code quality metric"""

    # Test with sample_input.txt
    input_file = "sample_input.txt"

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        return

    print(f"Debugging scoring with {input_file}")
    print("=" * 60)

    # Parse the input file
    parsed_entries = parse_input_file(input_file)

    for i, entry in enumerate(parsed_entries, 1):
        print(f"\nPROCESSING MODEL {i}: {entry['name']}")
        print("-" * 40)

        # Fetch metadata
        metadata = fetch_metadata(entry, debug=False)

        print("METADATA PASSED TO SCORER:")
        print(f"  name: {metadata.get('name')}")
        print(f"  category: {metadata.get('category')}")
        print(f"  url: {metadata.get('url')}")
        print(f"  code_url: {metadata.get('code_url', 'NOT FOUND')}")
        print(f"  dataset_url: {metadata.get('dataset_url', 'NOT FOUND')}")

        # Test code quality metric directly
        print("\nTESTING CODE QUALITY METRIC DIRECTLY:")
        cq_metric = code_quality()

        try:
            # Call get_data to see what it extracts
            cq_data = cq_metric.get_data(metadata)
            print("  Code quality get_data() returned:")
            print(f"    has_tests: {cq_data.get('has_tests', False)}")
            print(f"    has_ci: {cq_data.get('has_ci', False)}")
            print(f"    has_lint_config: {cq_data.get('has_lint_config', False)}")
            print(f"    python_file_count: {cq_data.get('python_file_count', 0)}")
            print(f"    has_readme: {cq_data.get('has_readme', False)}")
            print(f"    has_packaging: {cq_data.get('has_packaging', False)}")

            # Calculate score
            cq_metric.calculate_score(cq_data)
            score = cq_metric.get_score()
            latency = cq_metric.get_latency()

            print(f"  Code quality score: {score}")
            print(f"  Code quality latency: {latency}")

            # Break down the scoring
            print("\n  SCORE BREAKDOWN:")
            has_tests = bool(cq_data.get("has_tests", False))
            has_ci = bool(cq_data.get("has_ci", False))
            has_lint = bool(cq_data.get("has_lint_config", False))
            py_count = int(cq_data.get("python_file_count", 0))
            has_readme = bool(cq_data.get("has_readme", False))
            has_packaging = bool(cq_data.get("has_packaging", False))

            print(
                "    Tests (30%): "
                f"{1.0 if has_tests else 0.0} * 0.30 = "
                f"{(1.0 if has_tests else 0.0) * 0.30}"
            )
            print(
                f"    CI (25%): {1.0 if has_ci else 0.0} * 0.25 = {(1.0 if has_ci else 0.0) * 0.25}"
            )
            print(
                "    Linting (15%): "
                f"{1.0 if has_lint else 0.0} * 0.15 = "
                f"{(1.0 if has_lint else 0.0) * 0.15}"
            )
            py_score = min(1.0, py_count / 20.0)
            print(f"    Python files (15%): {py_score} * 0.15 = {py_score * 0.15}")
            doc_pack_score = (
                1.0
                if (has_readme and has_packaging)
                else (0.5 if (has_readme or has_packaging) else 0.0)
            )
            print(f"    Docs+Packaging (15%): {doc_pack_score} * 0.15 = {doc_pack_score * 0.15}")

            total_expected = (
                (1.0 if has_tests else 0.0) * 0.30
                + (1.0 if has_ci else 0.0) * 0.25
                + (1.0 if has_lint else 0.0) * 0.15
                + py_score * 0.15
                + doc_pack_score * 0.15
            )
            print(f"    TOTAL EXPECTED: {total_expected}")

            if score == 0.0:
                print("  [ERROR] Code quality scored 0 - investigating...")

                # Check if repo_url was found
                category = metadata.get("category", "")
                url = metadata.get("url", "")
                code_url = metadata.get("code_url", "")

                print(f"    category: {category}")
                print(f"    url: {url}")
                print(f"    code_url: {code_url}")

                repo_url = None
                if category == "CODE" and "github.com" in url:
                    repo_url = url
                    print(f"    [PATH 1] Found repo_url from CODE category: {repo_url}")
                elif category == "MODEL" and code_url and "github.com" in code_url:
                    repo_url = code_url
                    print(f"    [PATH 2] Found repo_url from MODEL code_url: {repo_url}")
                else:
                    print("    [ERROR] No repo_url found!")
                    print(f"      - category == 'MODEL': {category == 'MODEL'}")
                    print(f"      - code_url exists: {bool(code_url)}")
                    print(f"      - code_url has github.com: {'github.com' in (code_url or '')}")

        except Exception as e:
            print(f"  [ERROR] Code quality metric failed: {e}")

        # Test full scorer
        print("\nTESTING FULL SCORER:")
        scorer = Scorer()
        result = scorer.score(metadata)

        print(f"  Net score: {result.get('net_score')}")
        print(f"  Code quality from scorer: {result.get('code_quality')}")
        print(f"  Code quality latency: {result.get('code_quality_latency')}")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    debug_scoring()
