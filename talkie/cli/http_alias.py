"""`http` entrypoint: HTTPie-style `http GET url` → Talkie `get url`."""

import sys

_HTTP_METHODS = frozenset(
    ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")
)


def main() -> None:
    """Forward to Talkie CLI, mapping leading METHOD to subcommand."""
    argv = list(sys.argv[1:])
    if (
        len(argv) >= 2
        and not argv[0].startswith("-")
        and argv[0].upper() in _HTTP_METHODS
    ):
        argv = [argv[0].lower()] + argv[1:]
        sys.argv = [sys.argv[0]] + argv
    from talkie.cli.main import app

    app()
