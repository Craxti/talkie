#!/usr/bin/env python3
"""Script to run pylint on tests with relaxed rules."""

import sys
from scripts.pylint_runner import run_pylint


if __name__ == "__main__":
    exit_code = run_pylint("tests", ["--disable=C0303,E0401,C0411,E1120,E1124,W1514"])
    sys.exit(exit_code)
