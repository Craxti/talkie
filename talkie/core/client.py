"""HTTP client for making requests."""

from typing import Any, Dict, Optional, Union

import httpx
from httpx import Response
from .request_builder import RequestBuilder
from ..utils.logger import Logger

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
    
    def __init__(self, timeout: int = 30, verify: bool = True, follow_redirects: bool = True):
        """
        Initialize HTTP client with specified parameters.
        
        Args:
            timeout (int): Connection timeout in seconds. Default is 30.
            verify (bool): Whether to verify SSL certificates. Default is True.
            follow_redirects (bool): Whether to follow redirects. Default is True.
        """
        self.timeout = timeout
        self.verify = verify
        self.follow_redirects = follow_redirects
        self.client = httpx.Client(verify=True)
    
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
        
        # Create Timeout instance
        timeout_obj = httpx.Timeout(self.timeout)
        
        # Execute request based on method
        response = self.client.request(
            method=method,
            url=url,
            params=params,
            headers=headers,
            data=data,
            json=json_data,
            timeout=timeout_obj,
            files=files,
        )
        
        logger.debug(f"Received response: {response.status_code}")
        return response

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
            
        # Use timeout from request or client
        timeout = request.get("timeout", self.timeout)
        
        # Execute request
        return self.request(
            method=request["method"],
            url=request["url"],
            headers=request.get("headers"),
            params=request.get("params"),
            json_data=request.get("json"),
            data=request.get("data"),
            files=request.get("files"),
        )

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
        self.close() 