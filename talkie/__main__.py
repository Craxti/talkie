# -*- coding: utf-8 -*-
"""Entry point for the Talkie CLI application."""

import sys
from talkie.cli.main import cli


def main(args=None):
    """Main function to run the application."""
    if args is None:
        args = sys.argv[1:]
    return cli(args)


if __name__ == "__main__":
    sys.exit(main()) 