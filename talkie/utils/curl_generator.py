"""Module for generating curl commands from HTTP requests."""

import json
from typing import Dict, Any, Optional, Union
from urllib.parse import urlparse, parse_qs


def generate_curl_command(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Union[str, Dict[str, Any]]] = None,
    params: Optional[Dict[str, str]] = None,
    files: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
    follow_redirects: bool = True,
    verbose: bool = False,
    insecure: bool = False
) -> str:
    """Generate curl command from HTTP request parameters.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        url: Request URL
        headers: Request headers
        data: Request body data
        params: URL query parameters
        files: Files to upload (for multipart/form-data)
        cookies: Cookies to send
        timeout: Request timeout in seconds
        follow_redirects: Whether to follow redirects
        verbose: Whether to use verbose output
        insecure: Whether to skip SSL certificate verification

    Returns:
        str: Generated curl command
    """
    # Start with curl command
    cmd_parts = ["curl"]

    # Add method
    if method.upper() != "GET":
        cmd_parts.append(f"-X {method.upper()}")

    # Add headers
    if headers:
        for key, value in headers.items():
            # Escape quotes in header values
            escaped_value = value.replace('"', '\\"')
            cmd_parts.append(f'-H "{key}: {escaped_value}"')

    # Add cookies
    if cookies:
        cookie_string = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        cmd_parts.append(f'-b "{cookie_string}"')

    # Add data/body
    if data:
        if isinstance(data, dict):
            # Convert dict to JSON
            json_data = json.dumps(data, ensure_ascii=False)
            cmd_parts.append(f'-d \'{json_data}\'')
        else:
            # String data
            cmd_parts.append(f'-d \'{data}\'')

    # Add files (for multipart/form-data)
    if files:
        for field_name, file_path in files.items():
            cmd_parts.append(f'-F "{field_name}=@{file_path}"')

    # Add query parameters
    if params:
        # Parse existing URL to get base
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        # Add new parameters
        for key, value in params.items():
            query_params[key] = [value]

        # Rebuild URL with parameters
        new_query = "&".join([f"{k}={v[0]}" for k, v in query_params.items()])
        if new_query:
            separator = "&" if parsed_url.query else "?"
            url = f"{url}{separator}{new_query}"

    # Add options
    if timeout:
        cmd_parts.append(f"--max-time {timeout}")

    if not follow_redirects:
        cmd_parts.append("--location-trusted")

    if verbose:
        cmd_parts.append("-v")

    if insecure:
        cmd_parts.append("-k")

    # Add URL
    cmd_parts.append(f'"{url}"')

    return " ".join(cmd_parts)


def generate_curl_from_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Union[str, Dict[str, Any]]] = None,
    **kwargs
) -> str:
    """Generate curl command from request parameters.

    Args:
        method: HTTP method
        url: Request URL
        headers: Request headers
        data: Request data
        **kwargs: Additional curl options

    Returns:
        str: Generated curl command
    """
    return generate_curl_command(
        method=method,
        url=url,
        headers=headers,
        data=data,
        **kwargs
    )


def format_curl_for_display(curl_command: str, max_length: int = 100) -> str:
    """Format curl command for better display.

    Args:
        curl_command: Generated curl command
        max_length: Maximum line length

    Returns:
        str: Formatted curl command
    """
    if len(curl_command) <= max_length:
        return curl_command

    # Split long commands into multiple lines
    parts = curl_command.split()
    lines = []
    current_line = []

    for part in parts:
        if len(" ".join(current_line + [part])) > max_length:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [part]
            else:
                lines.append(part)
        else:
            current_line.append(part)

    if current_line:
        lines.append(" ".join(current_line))

    return " \\\n  ".join(lines)


def extract_curl_options(curl_command: str) -> Dict[str, Any]:
    """Extract options from curl command.

    Args:
        curl_command: Curl command string

    Returns:
        Dict[str, Any]: Extracted options
    """
    options = {}
    parts = curl_command.split()

    i = 0
    while i < len(parts):
        part = parts[i]

        if part.startswith("-"):
            if part == "-X":
                options["method"] = parts[i + 1]
                i += 1
            elif part == "-H":
                header = parts[i + 1]
                if ":" in header:
                    key, value = header.split(":", 1)
                    options.setdefault("headers", {})[key.strip()] = value.strip()
                i += 1
            elif part == "-d":
                options["data"] = parts[i + 1]
                i += 1
            elif part == "-b":
                options["cookies"] = parts[i + 1]
                i += 1
            elif part == "-k":
                options["insecure"] = True
            elif part == "-v":
                options["verbose"] = True
            elif part.startswith("--max-time"):
                options["timeout"] = int(part.split("=")[1])

        i += 1

    return options
