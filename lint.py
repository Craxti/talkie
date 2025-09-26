#!/usr/bin/env python3
"""Script to run pylint with proper configuration."""

import sys
from scripts.pylint_runner import run_pylint


if __name__ == "__main__":
    exit_code = run_pylint("talkie", ["--ignore=tests"])
    sys.exit(exit_code)
