"""Request builder for HTTP requests."""

from typing import Dict, Any


class RequestBuilder:
    """Builder for HTTP requests."""

    def __init__(self):
        self.method = "GET"
        self.url = ""
        self.headers = {}
        self.data = None
        self.params = {}

    def set_method(self, method: str) -> "RequestBuilder":
        """Set HTTP method."""
        self.method = method.upper()
        return self

    def set_url(self, url: str) -> "RequestBuilder":
        """Set request URL."""
        self.url = url
        return self

    def add_header(self, key: str, value: str) -> "RequestBuilder":
        """Add header."""
        self.headers[key] = value
        return self

    def set_data(self, data: Any) -> "RequestBuilder":
        """Set request data."""
        self.data = data
        return self

    def add_param(self, key: str, value: str) -> "RequestBuilder":
        """Add query parameter."""
        self.params[key] = value
        return self

    def build(self) -> Dict[str, Any]:
        """Build request dictionary."""
        return {
            "method": self.method,
            "url": self.url,
            "headers": self.headers,
            "data": self.data,
            "params": self.params
        }
