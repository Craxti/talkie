"""HTTP execution for CLI: config merge, URL resolution, history."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from talkie.core.client import HttpClient
from talkie.utils.config import Config, load_config
from talkie.utils.history import add_to_history


def parse_header_pairs(pairs: List[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for raw in pairs:
        if ":" not in raw:
            raise ValueError(f'Header must be "Name: value", got: {raw!r}')
        name, value = raw.split(":", 1)
        out[name.strip()] = value.strip()
    return out


def parse_query_pairs(pairs: List[str]) -> Dict[str, str]:
    params: Dict[str, str] = {}
    for raw in pairs:
        if "=" not in raw:
            raise ValueError(f'Query must be key=value, got: {raw!r}')
        k, v = raw.split("=", 1)
        params[k.strip()] = v.strip()
    return params


def parse_httpie_items(items: List[str]) -> Dict[str, Any]:
    """Parse `key=value` / `key:=json` items (httpie-style) into a JSON object."""
    body: Dict[str, Any] = {}
    for item in items:
        if ":=" in item:
            key, _, val = item.partition(":=")
            key = key.strip()
            val = val.strip()
            try:
                body[key] = json.loads(val)
            except json.JSONDecodeError:
                body[key] = val
        elif "=" in item:
            key, _, val = item.partition("=")
            body[key.strip()] = val
    return body


def resolve_url(url: str, config: Config) -> str:
    if url.startswith(("http://", "https://")):
        return url
    env = config.get_active_environment()
    base = (env.base_url if env else None) or ""
    if not base:
        raise ValueError(
            "Relative URL requires an active environment with base_url in ~/.talkie/config.json"
        )
    base = base.rstrip("/")
    path = url if url.startswith("/") else f"/{url}"
    return f"{base}{path}"


def merge_headers(config: Config, request_headers: Dict[str, str]) -> Dict[str, str]:
    merged: Dict[str, str] = dict(config.default_headers)
    env = config.get_active_environment()
    if env and env.default_headers:
        merged.update(env.default_headers)
    merged.update(request_headers)
    return merged


def execute_request(
    method: str,
    url: str,
    *,
    config: Optional[Config] = None,
    header_pairs: Optional[List[str]] = None,
    query_pairs: Optional[List[str]] = None,
    json_body: Optional[Any] = None,
    data_dict: Optional[Dict[str, Any]] = None,
    raw_body: Optional[str] = None,
    timeout: float = 30.0,
    verify: bool = True,
    follow_redirects: bool = True,
    record_history: bool = True,
) -> Dict[str, Any]:
    """Perform HTTP request; returns status, headers, body, elapsed_seconds, url, method."""
    cfg = config or load_config()
    full_url = resolve_url(url, cfg)
    req_headers = parse_header_pairs(header_pairs or [])
    headers = merge_headers(cfg, req_headers)
    params = parse_query_pairs(query_pairs) if query_pairs else {}

    req_kwargs: Dict[str, Any] = {"headers": headers}
    if params:
        req_kwargs["params"] = params
    if json_body is not None:
        req_kwargs["json"] = json_body
    elif raw_body is not None:
        req_kwargs["content"] = (
            raw_body.encode("utf-8") if isinstance(raw_body, str) else raw_body
        )
    elif data_dict:
        req_kwargs["data"] = data_dict

    with HttpClient(
        timeout=timeout,
        follow_redirects=follow_redirects,
        verify=verify,
    ) as hc:
        result = hc.request(method.upper(), full_url, **req_kwargs)

    elapsed = result.get("elapsed_seconds") or 0.0
    out = {
        "status": result["status"],
        "headers": result["headers"],
        "body": result["body"],
        "elapsed_seconds": elapsed,
        "url": full_url,
        "method": method.upper(),
        "request_headers": headers,
    }

    if record_history:
        hist_payload: Any = None
        if json_body is not None:
            hist_payload = json_body
        elif data_dict is not None:
            hist_payload = data_dict
        elif raw_body is not None:
            hist_payload = (
                raw_body[:5000] if isinstance(raw_body, str) and len(raw_body) > 5000 else raw_body
            )
        add_to_history(
            method=method.upper(),
            url=full_url,
            headers=headers,
            data=hist_payload,
            response_status=result["status"],
            response_time=elapsed,
        )

    return out
