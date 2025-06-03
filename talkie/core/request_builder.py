"""Module for building HTTP requests."""

import json
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from pydantic import BaseModel, Field, validator


class RequestBuilder:
    """HTTP request builder."""
    
    def __init__(
        self,
        method: str,
        url: str,
        headers: Optional[List[str]] = None,
        data: Optional[List[str]] = None,
        query: Optional[List[str]] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize request builder.
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Headers in format ["key:value", ...]
            data: Data in format ["key=value", "key:=value", ...]
            query: Query parameters in format ["key=value", ...]
            timeout: Request timeout in seconds
        """
        self.method = method.upper()
        self.url = url
        self.headers_list = headers or []
        self.data_list = data or []
        self.query_list = query or []
        self.timeout = timeout
        
        # Initialize data
        self.headers = {}
        self.data = {}
        self.json_data = {}
        self.query_params = {}
        
        # Parse parameters
        self._parse_headers()
        self._parse_data()
        self._parse_query()
    
    def _parse_headers(self) -> None:
        """Parse headers from "key:value" format."""
        for header in self.headers_list:
            if ":" in header:
                key, value = header.split(":", 1)
                key = key.strip()
                value = value.strip()
                if key:  # Skip headers with empty key
                    self.headers[key] = value
    
    def _parse_data(self) -> None:
        """Parse data from "key=value" or "key:=value" format for JSON."""
        form_data = {}
        json_data = {}
        has_json = False
        
        # First check if there are JSON data
        for item in self.data_list:
            if ":=" in item:
                has_json = True
                break
        
        # Process all data
        for item in self.data_list:
            if ":=" in item:  # JSON data
                key, value = item.split(":=", 1)
                key = key.strip()
                if not key:  # Skip data with empty key
                    continue
                try:
                    # Try to parse as JSON
                    if value.startswith("[") or value.startswith("{"):
                        json_value = json.loads(value)
                    elif value.lower() == "true":
                        json_value = True
                    elif value.lower() == "false":
                        json_value = False
                    elif value.isdigit():
                        json_value = int(value)
                    elif value.replace(".", "", 1).isdigit():
                        json_value = float(value)
                    else:
                        json_value = value
                    json_data[key] = json_value
                except json.JSONDecodeError:
                    json_data[key] = value
            else:  # Form data
                key, value = item.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key:  # Skip data with empty key
                    form_data[key] = value
                    if has_json:  # If there is JSON data, add regular fields too
                        json_data[key] = value
        
        # If there is JSON data, use it
        if has_json:
            self.json_data = json_data
            self.data = {}
        else:
            self.data = form_data
            self.json_data = {}
    
    def _parse_query(self) -> None:
        """Parse query parameters from "key=value" format."""
        for param in self.query_list:
            if "=" in param:
                key, value = param.split("=", 1)
                self.query_params[key.strip()] = value.strip()
    
    def apply_config(self, config: Any) -> None:
        """Apply settings from configuration.
        
        Args:
            config: Configuration object with default headers etc.
        """
        if hasattr(config, "default_headers") and config.default_headers:
            # Add headers from configuration if not already set
            for key, value in config.default_headers.items():
                if key not in self.headers:
                    self.headers[key] = value
    
    def build(self) -> Dict[str, Any]:
        """Build request.
        
        Returns:
            Dict[str, Any]: Dictionary with request parameters
        """
        request = {
            "method": self.method,
            "url": self.url,
            "timeout": self.timeout,
        }
        
        # Add headers
        if self.headers:
            request["headers"] = self.headers.copy()
        
        # Add query parameters
        if self.query_params:
            request["params"] = self.query_params
        
        # Add data
        if self.json_data:
            request["json"] = self.json_data
            if "headers" not in request:
                request["headers"] = {}
            request["headers"]["Content-Type"] = "application/json"
        elif self.data:
            request["data"] = self.data
            if "headers" not in request:
                request["headers"] = {}
            request["headers"]["Content-Type"] = "application/x-www-form-urlencoded"
        
        return request