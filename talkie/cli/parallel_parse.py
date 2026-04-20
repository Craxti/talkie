"""Parse one line from a `talkie parallel -f` file (README format)."""

from __future__ import annotations

import os
import shlex
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from talkie.cli.execute import parse_httpie_items

_METHODS = frozenset(
    ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")
)


@dataclass
class ParallelJob:
    """Single job for parallel execution."""

    method: str
    url: str
    json_body: Optional[Dict[str, Any]] = None


def parse_parallel_line(line: str) -> ParallelJob:
    """Parse lines like::

        GET https://api.example.com/users/1
        POST https://api.example.com/users -F name=John
        POST https://api.example.com/users name=John age:=30
    """
    raw = line.strip()
    if not raw or raw.startswith("#"):
        raise ValueError("empty or comment")
    try:
        parts = shlex.split(raw, posix=os.name != "nt")
    except ValueError:
        parts = raw.split()

    idx = 0
    method = "GET"
    if parts and parts[0].upper() in _METHODS:
        method = parts[0].upper()
        idx += 1
    if idx >= len(parts):
        raise ValueError(f"no URL in line: {line!r}")

    url = parts[idx]
    idx += 1
    fragments: List[str] = []
    while idx < len(parts):
        tok = parts[idx]
        if tok in ("-F", "--form"):
            if idx + 1 >= len(parts):
                raise ValueError(f"missing value after {tok} in {line!r}")
            fragments.append(parts[idx + 1])
            idx += 2
        elif "=" in tok or ":=" in tok:
            fragments.append(tok)
            idx += 1
        else:
            raise ValueError(f"unexpected token {tok!r} in {line!r}")

    json_body: Optional[Dict[str, Any]] = None
    if fragments:
        json_body = parse_httpie_items(fragments)

    return ParallelJob(method=method, url=url, json_body=json_body)
