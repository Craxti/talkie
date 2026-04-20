"""Parse a curl command line into components for replay with Talkie."""

from __future__ import annotations

import json
import logging
import os
import shlex
from typing import Any, Dict, List, Optional

logger = logging.getLogger("talkie.curl_parser")


def parse_curl_command(command: str) -> Dict[str, Any]:
    """Parse `curl ...` string (POSIX-style quoting). Returns method, url, headers, data, flags."""
    command = command.strip()
    if not command.lower().startswith("curl"):
        raise ValueError("Command must start with curl")

    try:
        tokens = shlex.split(command, posix=os.name != "nt")
    except ValueError as exc:
        logger.warning("shlex failed to parse curl: %s", exc)
        raise ValueError(f"Could not parse curl command: {exc}") from exc

    method = "GET"
    url: Optional[str] = None
    headers: Dict[str, str] = {}
    data: Optional[str] = None
    data_binary: Optional[bytes] = None
    insecure = False
    verbose = False

    i = 0
    while i < len(tokens):
        t = tokens[i]
        low = t.lower()

        if low == "curl":
            i += 1
            continue

        if low in ("-x", "--request"):
            method = tokens[i + 1].upper()
            i += 2
            continue

        if low in ("-h", "--header"):
            raw = tokens[i + 1]
            if ":" in raw:
                k, v = raw.split(":", 1)
                headers[k.strip()] = v.strip()
            i += 2
            continue

        if low in ("-d", "--data", "--data-raw"):
            data = tokens[i + 1]
            if method == "GET":
                method = "POST"
            i += 2
            continue

        if low == "--data-binary":
            data_binary = tokens[i + 1].encode("utf-8")
            if method == "GET":
                method = "POST"
            i += 2
            continue

        if low in ("-k", "--insecure"):
            insecure = True
            i += 1
            continue

        if low in ("-v", "--verbose"):
            verbose = True
            i += 1
            continue

        if t.startswith("-") and "=" in t:
            left, val = t.split("=", 1)
            if left.lower() in ("--url",):
                url = val
                i += 1
                continue

        if not t.startswith("-") and (t.startswith("http://") or t.startswith("https://")):
            url = t
            i += 1
            continue

        if low in ("--url",):
            url = tokens[i + 1]
            i += 2
            continue

        i += 1

    if not url:
        raise ValueError("No URL found in curl command")

    body: Any = data
    if data and (data.startswith("{") or data.startswith("[")):
        try:
            body = json.loads(data)
        except json.JSONDecodeError:
            body = data

    return {
        "method": method,
        "url": url,
        "headers": headers,
        "data": body,
        "data_binary": data_binary,
        "insecure": insecure,
        "verbose": verbose,
    }
