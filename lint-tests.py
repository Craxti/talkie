#!/usr/bin/env python3
"""Script to run pylint on tests with relaxed rules."""

import subprocess
import sys
from pathlib import Path


def run_pylint_tests():
    """Run pylint on test files with relaxed rules."""
    project_root = Path(__file__).parent
    
    cmd = [
        sys.executable, "-m", "pylint",
        "tests",
        "--score=y",
        "--reports=y",
        "--disable=C0303,E0401,C0411,E1120,E1124,W1514"
    ]
    
    try:
        result = subprocess.run(cmd, cwd=project_root, check=False)
        return result.returncode
    except Exception as e:
        print(f"Error running pylint on tests: {e}")
        return 1


if __name__ == "__main__":
    exit_code = run_pylint_tests()
    sys.exit(exit_code)
