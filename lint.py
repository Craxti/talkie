#!/usr/bin/env python3
"""Script to run pylint with proper configuration."""

import subprocess
import sys
from pathlib import Path


def run_pylint():
    """Run pylint on the talkie package."""
    project_root = Path(__file__).parent
    
    cmd = [
        sys.executable, "-m", "pylint",
        "talkie",
        "--score=y",
        "--reports=y"
    ]
    
    try:
        result = subprocess.run(cmd, cwd=project_root, check=False)
        return result.returncode
    except Exception as e:
        print(f"Error running pylint: {e}")
        return 1


if __name__ == "__main__":
    exit_code = run_pylint()
    sys.exit(exit_code)
