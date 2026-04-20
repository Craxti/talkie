"""HTTP client for Talkie."""

from typing import Any, Dict, Optional, Union

import httpx


class HttpClient:
    """Synchronous HTTP client wrapping httpx."""

    def __init__(
        self,
        timeout: Union[float, httpx.Timeout] = 30.0,
        follow_redirects: bool = True,
        verify: bool = True,
    ) -> None:
        self._timeout = timeout
        self._follow_redirects = follow_redirects
        self._verify = verify
        self.client: Optional[httpx.Client] = None

    def __enter__(self) -> "HttpClient":
        self.client = httpx.Client(
            timeout=self._timeout,
            follow_redirects=self._follow_redirects,
            verify=self._verify,
        )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.client:
            self.client.close()
            self.client = None

    def request(self, method: str, url: str, **kwargs: Any) -> Dict[str, Any]:
        """Make HTTP request; returns status, headers, body, elapsed_seconds."""
        if not self.client:
            raise RuntimeError("Client not initialized; use 'with HttpClient() as client:'")

        response = self.client.request(method, url, **kwargs)
        elapsed = getattr(response, "elapsed", None)
        elapsed_s = elapsed.total_seconds() if elapsed is not None else None
        return {
            "status": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
            "elapsed_seconds": elapsed_s,
            "response": response,
        }
