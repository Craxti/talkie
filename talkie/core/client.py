"""HTTP client for Talkie."""

from typing import Dict, Any, Optional
import httpx


class HttpClient:
    """HTTP client."""

    def __init__(self):
        self.client: Optional[httpx.Client] = None

    def __enter__(self):
        """Enter context manager."""
        self.client = httpx.Client()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self.client:
            self.client.close()
            self.client = None

    def request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request."""
        if not self.client:
            raise RuntimeError("Client not initialized")

        response = self.client.request(method, url, **kwargs)
        return {
            "status": response.status_code,
            "headers": dict(response.headers),
            "body": response.text
        }
