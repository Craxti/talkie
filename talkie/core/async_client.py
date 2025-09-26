"""Async HTTP client for Talkie."""

from typing import Dict, Any, Optional
import httpx


class AsyncHttpClient:
    """Async HTTP client."""

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Enter async context manager."""
        self.client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make async HTTP request."""
        if not self.client:
            raise RuntimeError("Client not initialized")

        response = await self.client.request(method, url, **kwargs)
        return {
            "status": response.status_code,
            "headers": dict(response.headers),
            "body": response.text
        }
