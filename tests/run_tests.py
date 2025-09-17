#!/usr/bin/env python3
"""
Test runner utility for AI Sandbox tests.
Automatically sets up the correct Python path for all tests.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def get_project_root():
    """Get the project root directory (parent of tests/)."""
    return Path(__file__).parent.parent


def run_test(test_path, args=None):
    """Run a test with the correct Python path."""
    project_root = get_project_root()

    # Set up environment
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    # Build command
    cmd = [sys.executable, test_path]
    if args:
        cmd.extend(args)

    print(f"Running: {' '.join(cmd)}")
    print(f"Project root: {project_root}")
    print("-" * 60)

    # Run the test
    result = subprocess.run(cmd, env=env, cwd=project_root)
    return result.returncode


def list_tests():
    """List all available tests."""
    tests_dir = Path(__file__).parent

    categories = {
        "balance": "Balance and economy tests",
        "population": "Population dynamics tests",
        "markov": "Markov chain and dialogue tests",
        "integration": "System integration tests",
        "environmental": "Environmental AI tests",
        "system": "Core system functionality tests",
        "specialized": "Specialized feature tests",
        "demos": "Demonstration scripts",
    }

    print("Available Tests:")
    print("=" * 50)

    for category, description in categories.items():
        category_dir = tests_dir / category
        if category_dir.exists():
            print(f"\n{category.upper()}: {description}")
            for test_file in sorted(category_dir.glob("*.py")):
                print(f"  {category}/{test_file.name}")


def run_category(category):
    """Run all tests in a category."""
    tests_dir = Path(__file__).parent
    category_dir = tests_dir / category

    if not category_dir.exists():
        print(f"Category '{category}' not found.")
        return 1

    test_files = list(category_dir.glob("*.py"))
    if not test_files:
        print(f"No test files found in category '{category}'.")
        return 1

    print(f"Running all tests in category: {category}")
    print("=" * 60)

    failed_tests = []
    for test_file in sorted(test_files):
        print(f"\n>>> Running {category}/{test_file.name}")
        return_code = run_test(str(test_file))
        if return_code != 0:
            failed_tests.append(f"{category}/{test_file.name}")
        print(f"<<< {category}/{test_file.name} completed with code {return_code}")

    if failed_tests:
        print(f"\n❌ {len(failed_tests)} test(s) failed:")
        for test in failed_tests:
            print(f"  - {test}")
        return 1
    else:
        print(f"\n✅ All {len(test_files)} tests in '{category}' passed!")
        return 0


def main():
    parser = argparse.ArgumentParser(description="AI Sandbox Test Runner")
    parser.add_argument("--list", action="store_true", help="List all available tests")
    parser.add_argument("--category", help="Run all tests in a category")
    parser.add_argument("test_path", nargs="?", help="Path to specific test file")
    parser.add_argument("test_args", nargs="*", help="Arguments to pass to the test")

    args = parser.parse_args()

    if args.list:
        list_tests()
        return 0

    if args.category:
        return run_category(args.category)

    if args.test_path:
        return run_test(args.test_path, args.test_args)

    # No arguments provided, show help
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
