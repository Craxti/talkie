"""
Asynchronous HTTP client for parallel request execution.
"""

import asyncio
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import httpx
from httpx import Response
from pydantic import BaseModel, Field, validator
from ..utils.logger import Logger
import json

logger = Logger()


class RequestConfig(BaseModel):
    """
    Configuration for HTTP request.
    
    Attributes:
        method (str): HTTP method (GET, POST etc.)
        url (str): Request URL
        headers (Dict[str, str], optional): HTTP headers
        params (Dict[str, Any], optional): Query parameters
        json_data (Dict[str, Any], optional): JSON data
        data (Dict[str, Any], optional): Form data
        files (Dict[str, Any], optional): Files to upload
        timeout (float): Timeout in seconds
        verify (bool): Whether to verify SSL certificates
        follow_redirects (bool): Whether to follow redirects
        id (Optional[str]): Request ID (for tracking)
    """
    method: str
    url: str
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    json_data: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    files: Optional[Dict[str, Any]] = None
    timeout: float = 30.0
    verify: bool = True
    follow_redirects: bool = True
    id: Optional[str] = None


class AsyncHttpClient:
    """
    Asynchronous HTTP client for parallel request execution.
    
    The class provides an interface for sending multiple HTTP requests
    in parallel, which significantly speeds up processing of large
    number of requests.
    
    Attributes:
        timeout (int): Connection timeout in seconds.
        verify (bool): Whether to verify SSL certificates.
        follow_redirects (bool): Whether to follow redirects.
        max_connections (int): Maximum number of simultaneous connections.
        request_delay (float): Delay between requests in seconds.
    
    Examples:
        >>> async with AsyncHttpClient(concurrency=5) as client:
        >>>     responses = await client.execute_batch(requests)
        >>>     for resp in responses:
        >>>         print(resp.status_code)
    """
    
    def __init__(
        self, 
        timeout: int = 30, 
        verify: bool = True, 
        follow_redirects: bool = True,
        concurrency: int = 10,
        request_delay: float = 0.0
    ):
        """
        Initialize asynchronous HTTP client with specified parameters.
        
        Args:
            timeout (int): Connection timeout in seconds. Default is 30.
            verify (bool): Whether to verify SSL certificates. Default is True.
            follow_redirects (bool): Whether to follow redirects. Default is True.
            concurrency (int): Maximum number of simultaneous requests. Default is 10.
            request_delay (float): Delay between requests in seconds. Default is 0.
        """
        self.timeout = timeout
        self.verify = verify
        self.follow_redirects = follow_redirects
        self.concurrency = concurrency
        self.request_delay = request_delay
        # Client will be initialized when entering context manager
        self.client = None
        # Semaphore for limiting simultaneous requests
        self.semaphore = asyncio.Semaphore(concurrency)
    
    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> Tuple[Optional[str], httpx.Response]:
        """
        Execute asynchronous HTTP request with specified parameters.
        
        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE etc.).
            url (str): Request URL.
            headers (Dict[str, str], optional): Request headers.
            params (Dict[str, Any], optional): Query string parameters.
            json_data (Dict[str, Any], optional): JSON data.
            data (Dict[str, Any], optional): Form data.
            files (Dict[str, Any], optional): Files to upload.
            request_id (Optional[str]): Request ID for tracking.
            
        Returns:
            Tuple[Optional[str], httpx.Response]: Request ID and response object.
            
        Raises:
            httpx.RequestError: If request cannot be completed.
            httpx.HTTPStatusError: If response contains error code (4xx, 5xx).
        """
        if self.client is None:
            raise RuntimeError("Client not initialized. Use context manager.")
        
        req_desc = f"[{request_id or 'N/A'}] {method} {url}"
        logger.debug(f"Executing request: {req_desc}")
        
        async with self.semaphore:
            # Add optional delay between requests
            if self.request_delay > 0:
                await asyncio.sleep(self.request_delay)
                
            # Create Timeout instance
            timeout_obj = httpx.Timeout(self.timeout)
            
            try:
                # Execute request
                response = await self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                    data=data,
                    json=json_data,
                    timeout=timeout_obj,
                    files=files,
                )
                
                logger.debug(f"Received response: {req_desc} -> {response.status_code}")
                return request_id, response
                
            except httpx.RequestError as e:
                logger.error(f"Request error: {req_desc} -> {str(e)}")
                raise
    
    async def execute_batch(
        self, 
        requests: List[Dict[str, Any]]
    ) -> List[Tuple[Optional[str], Optional[httpx.Response], Optional[Exception]]]:
        """
        Execute batch request processing in parallel.
        
        Args:
            requests (List[Dict[str, Any]]): List of requests to execute.
                Each request must contain keys: method, url and optionally
                headers, params, json, data, files, request_id.
                
        Returns:
            List[Tuple[Optional[str], Optional[Response], Optional[Exception]]]: 
                List of tuples (request ID, response, exception).
                If request was successful, exception will be None.
                If request failed, response will be None.
        """
        if self.client is None:
            raise RuntimeError("Client not initialized. Use context manager.")
            
        async def _execute_request(req: Dict[str, Any]) -> Tuple[Optional[str], Optional[httpx.Response], Optional[Exception]]:
            request_id = req.get("request_id")
            
            try:
                _, response = await self.request(
                    method=req["method"],
                    url=req["url"],
                    headers=req.get("headers"),
                    params=req.get("params"),
                    json_data=req.get("json"),
                    data=req.get("data"),
                    files=req.get("files"),
                    request_id=request_id,
                )
                return request_id, response, None
            except Exception as e:
                return request_id, None, e
        
        # Launch all requests in parallel and wait for completion
        tasks = [_execute_request(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        return results
    
    async def execute_from_file(self, file_path: str, output_dir: Optional[str] = None) -> List[Tuple[str, Optional[Response], Optional[str]]]:
        """Execute requests from file.
        
        Args:
            file_path: Path to file with requests
            output_dir: Directory to save results
            
        Returns:
            List[Tuple[str, Optional[Response], Optional[str]]]: List of results (id, response, error)
        """
        results = []
        request_count = 0
        
        # First count total number of valid requests
        valid_requests = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2 and parts[0].upper() in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
                    valid_requests.append(line)
        
        total_requests = len(valid_requests)
        
        # Execute valid requests
        for line in valid_requests:
            try:
                # Parse request string
                parts = line.split()
                method = parts[0].upper()
                url = parts[1]
                
                # Additional request parameters (if any)
                headers = {}
                params = {}
                data = {}
                
                # Parse additional parameters
                for param in parts[2:]:
                    if ":" in param:  # Header
                        key, value = param.split(":", 1)
                        headers[key.strip()] = value.strip()
                    elif "=" in param:  # Query parameter or data
                        key, value = param.split("=", 1)
                        if key.startswith("@"):  # Form data
                            data[key[1:].strip()] = value.strip()
                        else:  # Query parameter
                            params[key.strip()] = value.strip()
                
                # Execute request
                request_count += 1
                request_id = f"req_{request_count:04d}"  # Format with leading zeros
                
                _, response = await self.request(
                    method=method,
                    url=url,
                    headers=headers if headers else None,
                    params=params if params else None,
                    data=data if data else None,
                    request_id=request_id
                )
                
                # Save result to file if directory specified
                if output_dir:
                    output_file = os.path.join(output_dir, f"{request_id}.json")
                    with open(output_file, "w", encoding="utf-8") as out:
                        # Save full request and response information
                        result_data = {
                            "request": {
                                "method": method,
                                "url": url,
                                "headers": headers,
                                "params": params,
                                "data": data
                            },
                            "response": {
                                "status_code": response.status_code,
                                "headers": dict(response.headers),
                                "content": response.text
                            }
                        }
                        json.dump(result_data, out, indent=2, ensure_ascii=False)
                
                # Add result to list (id, response, error)
                results.append((request_id, response, None))
                
                # Log progress
                logger.debug(f"Executed request {request_count}/{total_requests}: {method} {url}")
                
            except Exception as e:
                logger.error(f"Error executing request {request_count}/{total_requests}: {e}")
                results.append((f"req_{request_count:04d}", None, str(e)))
                continue
        
        return results
    
    async def __aenter__(self) -> "AsyncHttpClient":
        """Enter asynchronous context manager."""
        self.client = httpx.AsyncClient(
            verify=self.verify,
            follow_redirects=self.follow_redirects,
            timeout=self.timeout,
        )
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit asynchronous context manager."""
        if self.client:
            await self.client.aclose()
            self.client = None 