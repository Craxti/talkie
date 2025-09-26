"""HTTP client for making requests."""

from typing import Any, Dict, Optional, Union, Tuple
import os

import httpx
from httpx import Response
from ..utils.logger import Logger
from ..utils.cache import get_cache

logger = Logger()


class HttpClient:
    """
    HTTP client for making requests.

    Provides methods for sending HTTP requests with various parameters
    and handling responses.

    Examples:
        >>> client = HttpClient()
        >>> response = client.get("https://api.example.com/users")
        >>> print(response.status_code)
    """

    def __init__(self,
                 timeout: int = 30,
                 verify: bool = True,
                 follow_redirects: bool = True,
                 cert: Optional[Union[str, Tuple[str, str]]] = None,
                 enable_cache: bool = True,
                 max_connections: int = 100,
                 max_keepalive_connections: int = 20):
        """
        Initialize HTTP client with specified parameters.

        Args:
            timeout (int): Connection timeout in seconds. Default is 30.
            verify (bool): Whether to verify SSL certificates. Default is True.
            follow_redirects (bool): Whether to follow redirects. Default is True.
            cert (Optional[Union[str, Tuple[str, str]]]): Client certificate.
                Can be a path to a .pem file or a tuple of (cert_file, key_file) paths.
            enable_cache (bool): Enable response caching. Default is True.
            max_connections (int): Maximum number of connections in pool. Default is 100.
            max_keepalive_connections (int): Maximum keepalive connections. Default is 20.
        """
        self.timeout = timeout
        self.verify = verify
        self.follow_redirects = follow_redirects
        self.cert = cert
        self.enable_cache = enable_cache
        self.max_connections = max_connections
        self.max_keepalive_connections = max_keepalive_connections

        # Initialize cache
        self.cache = get_cache() if enable_cache else None

        # Validate certificate files if provided
        if cert:
            self._validate_cert_files(cert)

        # Create optimized HTTP client with connection pooling
        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections
        )

        self.client = httpx.Client(
            verify=self.verify,
            follow_redirects=self.follow_redirects,
            timeout=httpx.Timeout(timeout),
            cert=self.cert,
            limits=limits
        )

    def _validate_cert_files(self, cert: Union[str, Tuple[str, str]]) -> None:
        """
        Validate certificate files exist and are readable.

        Args:
            cert: Certificate path or tuple of (cert_file, key_file)

        Raises:
            ValueError: If certificate files don't exist or aren't readable
        """
        if isinstance(cert, str):
            # Single .pem file
            if not os.path.isfile(cert):
                raise ValueError(f"Certificate file not found: {cert}")
            if not os.access(cert, os.R_OK):
                raise ValueError(f"Certificate file not readable: {cert}")
        elif isinstance(cert, tuple) and len(cert) == 2:
            # Separate cert and key files
            cert_file, key_file = cert
            if not os.path.isfile(cert_file):
                raise ValueError(f"Certificate file not found: {cert_file}")
            if not os.path.isfile(key_file):
                raise ValueError(f"Key file not found: {key_file}")
            if not os.access(cert_file, os.R_OK):
                raise ValueError(f"Certificate file not readable: {cert_file}")
            if not os.access(key_file, os.R_OK):
                raise ValueError(f"Key file not readable: {key_file}")
        else:
            raise ValueError("cert must be a string (path to .pem file) or tuple (cert_file, key_file)")

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Response:
        """
        Perform HTTP request with specified parameters.

        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE etc.).
            url (str): Request URL.
            headers (Dict[str, str], optional): Request headers.
            params (Dict[str, Any], optional): Query string parameters.
            json_data (Dict[str, Any], optional): JSON data.
            data (Dict[str, Any], optional): Form data.
            files (Dict[str, Any], optional): Files to upload.

        Returns:
            httpx.Response: Response object.

        Raises:
            httpx.RequestError: If request cannot be completed.
            httpx.HTTPStatusError: If response contains error code (4xx, 5xx).
        """
        logger.debug(f"Executing {method} request to {url}")

        # Check cache first if enabled
        if self.cache and self.enable_cache:
            # Prepare body for cache key
            cache_body = None
            if json_data:
                import json
                cache_body = json.dumps(json_data, sort_keys=True)
            elif data:
                cache_body = str(data)

            cached_response = self.cache.get_cached_response(
                method=method,
                url=url,
                headers=headers,
                params=params,
                body=cache_body
            )

            if cached_response:
                logger.debug(f"Cache hit for {method} {url}")
                return cached_response

        try:
            # Execute request
            response = self.client.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                data=data,
                json=json_data,
                files=files,
            )

            logger.debug(f"Received response: {response.status_code}")

            # Cache successful responses if caching is enabled
            if (self.cache and self.enable_cache and
                200 <= response.status_code < 300):
                # Only cache GET requests and responses under 1MB
                if (method.upper() == "GET" and
                    len(response.content) < 1024 * 1024):
                    self.cache.cache_response(response)

            # Check for HTTP errors
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise

            return response

        except httpx.TimeoutException as e:
            error_msg = f"Request timeout after {self.timeout} seconds"
            logger.error(error_msg)
            raise httpx.RequestError(error_msg) from e

        except httpx.ConnectError as e:
            error_msg = f"Failed to connect to {url}: {str(e)}"
            logger.error(error_msg)
            raise httpx.RequestError(error_msg) from e

        except httpx.NetworkError as e:
            error_msg = f"Network error occurred: {str(e)}"
            logger.error(error_msg)
            raise httpx.RequestError(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error during request: {str(e)}"
            logger.error(error_msg)
            raise httpx.RequestError(error_msg) from e

    def send(self, request: Dict[str, Any]) -> Response:
        """
        Send HTTP request based on parameter dictionary.

        Args:
            request (Dict[str, Any]): Request parameter dictionary.
                Must contain keys: 'method', 'url'.
                May contain keys: 'headers', 'params', 'json', 'data', 'files', 'timeout'.

        Returns:
            httpx.Response: Response object.

        Examples:
            >>> client = HttpClient()
            >>> request = {
            ...     "method": "GET",
            ...     "url": "https://api.example.com/users",
            ...     "headers": {"Accept": "application/json"},
            ...     "params": {"page": "1"}
            ... }
            >>> response = client.send(request)
        """
        # Check required keys
        if "method" not in request:
            raise ValueError("Request is missing required key 'method'")
        if "url" not in request:
            raise ValueError("Request is missing required key 'url'")

        # Use timeout from request if provided
        timeout = request.get("timeout", self.timeout)

        # Temporarily update client timeout if different
        original_timeout = self.timeout
        if timeout != self.timeout:
            self.timeout = timeout
            self.client.timeout = httpx.Timeout(timeout)

        try:
            # Execute request
            response = self.request(
                method=request["method"],
                url=request["url"],
                headers=request.get("headers"),
                params=request.get("params"),
                json_data=request.get("json"),
                data=request.get("data"),
                files=request.get("files"),
            )
            return response
        finally:
            # Restore original timeout if changed
            if timeout != original_timeout:
                self.timeout = original_timeout
                self.client.timeout = httpx.Timeout(original_timeout)

    def get(
        self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None
    ) -> Response:
        """
        Perform GET request to specified URL.

        Args:
            url (str): Request URL.
            headers (Dict[str, str], optional): Request headers.
            params (Dict[str, Any], optional): Query string parameters.

        Returns:
            httpx.Response: Response object.

        Examples:
            >>> client = HttpClient()
            >>> response = client.get("https://api.example.com/users",
            ...                      params={"page": 1, "limit": 10})
        """
        return self.request("GET", url, headers=headers, params=params)

    def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Response:
        """
        Perform POST request to specified URL.

        Args:
            url (str): Request URL.
            headers (Dict[str, str], optional): Request headers.
            params (Dict[str, Any], optional): Query string parameters.
            json_data (Dict[str, Any], optional): JSON data.
            data (Dict[str, Any], optional): Form data.
            files (Dict[str, Any], optional): Files to upload.

        Returns:
            httpx.Response: Response object.

        Examples:
            >>> client = HttpClient()
            >>> response = client.post("https://api.example.com/users",
            ...                       json_data={"name": "John", "age": 30})
        """
        return self.request(
            "POST", url, headers=headers, params=params, json_data=json_data, data=data, files=files
        )

    def close(self) -> None:
        """Close client connections."""
        self.client.close()

    def __enter__(self) -> "HttpClient":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        self.close()data, data=data, files=files
        )

    def close(self) -> None:
        """Close client connections."""
        self.client.close()

    def __enter__(self) -> "HttpClient":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        self.close()