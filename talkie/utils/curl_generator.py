"""Module for generating curl commands."""

import json
import shlex
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.syntax import Syntax


class CurlGenerator:
    """Class for generating curl commands from Talkie requests."""

    @staticmethod
    def generate_curl(
        method: str,
        url: str,
        headers: Dict[str, str] = None,
        data: Dict[str, str] = None,
        json_data: Dict[str, Any] = None,
        query_params: Dict[str, str] = None,
        form_data: Dict[str, str] = None,
        verbose: bool = False,
        insecure: bool = False,
    ) -> str:
        """Generate curl command from request parameters.

        Args:
            method: HTTP method
            url: URL address
            headers: HTTP headers
            data: Data to send as application/x-www-form-urlencoded
            json_data: JSON data to send as application/json
            query_params: Query parameters
            form_data: Form data to send as multipart/form-data
            verbose: Enable verbose output (-v)
            insecure: Do not verify SSL certificate (-k)

        Returns:
            str: curl command
        """
        headers = headers or {}
        data = data or {}
        json_data = json_data or {}
        query_params = query_params or {}
        form_data = form_data or {}

        # Start command
        command = ["curl"]

        # Curl settings
        if verbose:
            command.append("-v")
        if insecure:
            command.append("-k")
        
        # HTTP method
        if method.upper() != "GET":
            command.append(f"-X {method.upper()}")
        
        # Headers
        for key, value in headers.items():
            command.append(f"-H '{key}: {value}'")
        
        # Request data
        if json_data:
            if "Content-Type" not in headers:
                command.append("-H 'Content-Type: application/json'")
            json_str = json.dumps(json_data)
            command.append(f"-d '{json_str}'")
        elif data:
            if "Content-Type" not in headers:
                command.append("-H 'Content-Type: application/x-www-form-urlencoded'")
            data_str = "&".join([f"{key}={value}" for key, value in data.items()])
            command.append(f"-d '{data_str}'")
        elif form_data:
            for key, value in form_data.items():
                command.append(f"-F '{key}={value}'")
        
        # Build URL with query parameters
        if query_params:
            query_str = "&".join([f"{key}={value}" for key, value in query_params.items()])
            url = f"{url}{'?' if '?' not in url else '&'}{query_str}"
        
        # Add URL
        command.append(f"'{url}'")
        
        return " ".join(command)

    @staticmethod
    def generate_from_request(request: Dict[str, Any]) -> str:
        """Generate curl command from Talkie request.

        Args:
            request: Dictionary with request parameters

        Returns:
            str: curl command
        """
        return CurlGenerator.generate_curl(
            method=request.get("method", "GET"),
            url=request.get("url", ""),
            headers=request.get("headers", {}),
            data=request.get("data", {}),
            json_data=request.get("json", {}),
            query_params=request.get("params", {}),
            verbose=request.get("verbose", False),
            insecure=request.get("insecure", False),
        )

    @staticmethod
    def display_curl(curl_command: str, console: Optional[Console] = None) -> None:
        """Display curl command with syntax highlighting.

        Args:
            curl_command: curl command
            console: Rich console for output
        """
        if console is None:
            console = Console()
        
        syntax = Syntax(curl_command, "bash", theme="monokai", word_wrap=True)
        console.print(syntax)


def convert_dict_to_curl_args(data: Dict[str, Any]) -> List[str]:
    """Convert dictionary to curl arguments.

    Args:
        data: Dictionary with parameters

    Returns:
        List[str]: List of arguments
    """
    args = []
    for key, value in data.items():
        if isinstance(value, bool):
            args.append(f"{key}={str(value).lower()}")
        elif isinstance(value, (int, float)):
            args.append(f"{key}={value}")
        else:
            args.append(f"{key}={shlex.quote(str(value))}")
    return args 