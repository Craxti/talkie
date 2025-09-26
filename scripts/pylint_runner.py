#!/usr/bin/env python3
"""Common pylint runner module."""

import subprocess
import sys
from pathlib import Path


def run_pylint(target: str, additional_args: list = None):
    """Run pylint on specified target.
    
    Args:
        target: Target to lint (e.g., 'talkie', 'tests')
        additional_args: Additional pylint arguments
        
    Returns:
        Exit code from pylint
    """
    project_root = Path(__file__).parent.parent
    
    cmd = [
        sys.executable, "-m", "pylint",
        target,
        "--score=y",
        "--reports=y"
    ]
    
    if additional_args:
        cmd.extend(additional_args)
    
    try:
        result = subprocess.run(cmd, cwd=project_root, check=False)
        return result.returncode
    except Exception as e:
        print(f"Error running pylint: {e}")
        return 1
