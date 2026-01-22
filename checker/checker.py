#!/usr/bin/env python3
"""
Checker script for the Practice Problem: Contact Information Parser

Usage:
    python checker.py --url http://localhost:8000
"""

import requests
import json
import sys
import argparse
from pathlib import Path


def normalize(value):
    """Normalize values for comparison."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip().lower()
    return value


def check_health(base_url: str) -> bool:
    """Check if the server is healthy."""
    print("Checking server health...", end=" ")
    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        if r.status_code != 200:
            print(f"FAILED (status code: {r.status_code})")
            return False
        data = r.json()
        if data.get("status") != "ok":
            print(f"FAILED (status: {data.get('status')})")
            return False
        if data.get("database") != "connected":
            print(f"FAILED (database: {data.get('database')})")
            return False
        print("OK")
        return True
    except requests.exceptions.ConnectionError:
        print("FAILED (connection refused - is your server running?)")
        return False
    except Exception as e:
        print(f"FAILED ({e})")
        return False


def run_tests(base_url: str, test_cases_path: Path) -> tuple[int, int]:
    """Run all test cases and return (passed, total)."""
    with open(test_cases_path) as f:
        tests = json.load(f)

    passed = 0
    total = len(tests)

    print(f"\nRunning {total} test cases...\n")
    print("-" * 60)

    for i, test in enumerate(tests, 1):
        text = test["text"]
        expected = test["expected"]

        # Truncate text for display
        display_text = text[:50] + "..." if len(text) > 50 else text
        print(f"Test {i}: \"{display_text}\"")

        try:
            r = requests.post(
                f"{base_url}/parse",
                json={
                    "text": text,
                    "llm": "gemini-2.5-flash"
                },
                timeout=30
            )

            if r.status_code != 200:
                print(f"  FAILED - HTTP {r.status_code}")
                continue

            result = r.json()

            # Check each field
            all_match = True
            for field in ["name", "email", "phone", "company"]:
                exp_val = normalize(expected.get(field))
                got_val = normalize(result.get(field))

                if exp_val != got_val:
                    all_match = False
                    print(f"  FAILED - {field}: expected '{expected.get(field)}', got '{result.get(field)}'")

            # Check found_in_database (boolean comparison)
            exp_found = expected.get("found_in_database")
            got_found = result.get("found_in_database")
            if exp_found != got_found:
                all_match = False
                print(f"  FAILED - found_in_database: expected {exp_found}, got {got_found}")

            if all_match:
                passed += 1
                print(f"  PASSED")

        except requests.exceptions.Timeout:
            print(f"  FAILED - Request timed out")
        except json.JSONDecodeError:
            print(f"  FAILED - Invalid JSON response")
        except Exception as e:
            print(f"  FAILED - {e}")

    print("-" * 60)
    return passed, total


def main():
    parser = argparse.ArgumentParser(
        description="Test your Contact Parser API against test cases"
    )
    parser.add_argument(
        "--url", "-u",
        default="http://localhost:8000",
        help="Base URL of your server (default: http://localhost:8000)"
    )
    args = parser.parse_args()

    base_url = args.url.rstrip('/')

    # Determine test cases path (same directory as this script)
    script_dir = Path(__file__).parent
    test_cases_path = script_dir / "test_cases.json"

    if not test_cases_path.exists():
        print(f"Error: test_cases.json not found at {test_cases_path}")
        sys.exit(1)

    print(f"Testing server at: {base_url}")
    print("=" * 60)

    # Health check
    if not check_health(base_url):
        print("\nServer health check failed. Make sure your server is running.")
        sys.exit(1)

    # Run tests
    passed, total = run_tests(base_url, test_cases_path)

    # Summary
    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\nCongratulations! All tests passed!")
        print("You're ready for the main challenge.")
    elif passed >= total // 2:
        print("\nGood progress! Keep working on the failing cases.")
    else:
        print("\nKeep going! Check the error messages above for hints.")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
