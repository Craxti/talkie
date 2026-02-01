"""Main CLI module for Talkie."""

import sys

from talkie import __version__


def main():
    """Main entry point."""
    print("Talkie CLI - HTTP Client")
    print(f"Version: {__version__}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
