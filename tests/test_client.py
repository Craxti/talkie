"""Tests for HTTP client."""

import pytest
from unittest.mock import Mock, patch
import httpx
from talkie.core.client import HttpClient
from talkie.core.async_client import AsyncHttpClient


class TestHttpClient:
    """Test HTTP client."""
    
    def test_client_initialization(self):
        """Test client initialization."""
        client = HttpClient()
        assert client.client is None

    def test_context_manager(self):
        """Test context manager functionality."""
        client = HttpClient()
        assert client.client is None
        
        with client:
            assert client.client is not None
            assert isinstance(client.client, httpx.Client)
        
        # Client should be closed after context
        assert client.client is None

    def test_request_success(self):
        """Test successful HTTP request."""
        with HttpClient() as client:
            # Mock the httpx client
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.text = '{"result": "success"}'
            
            client.client.request = Mock(return_value=mock_response)
            
            result = client.request("GET", "https://example.com")
            
            assert result["status"] == 200
            assert result["headers"]["Content-Type"] == "application/json"
            assert result["body"] == '{"result": "success"}'

    def test_request_without_context(self):
        """Test request without context manager."""
        client = HttpClient()
        
        with pytest.raises(RuntimeError, match="Client not initialized"):
            client.request("GET", "https://example.com")

    def test_request_with_kwargs(self):
        """Test request with additional kwargs."""
        with HttpClient() as client:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.headers = {"Location": "https://example.com/resource/1"}
            mock_response.text = '{"id": 1}'
            
            client.client.request = Mock(return_value=mock_response)
            
            result = client.request(
                "POST", 
                "https://example.com",
                json={"name": "test"},
                headers={"Authorization": "Bearer token"}
            )
            
            assert result["status"] == 201
            assert result["headers"]["Location"] == "https://example.com/resource/1"
            assert result["body"] == '{"id": 1}'
            
            # Verify the request was called with correct parameters
            client.client.request.assert_called_once_with(
                "POST",
                "https://example.com",
                json={"name": "test"},
                headers={"Authorization": "Bearer token"}
            )

    def test_request_error_handling(self):
        """Test request error handling."""
        with HttpClient() as client:
            # Mock httpx to raise an exception
            client.client.request = Mock(side_effect=httpx.RequestError("Network error"))
            
            with pytest.raises(httpx.RequestError):
                client.request("GET", "https://example.com")


class TestAsyncHttpClient:
    """Test async HTTP client."""
    
    def test_async_client_initialization(self):
        """Test async client initialization."""
        client = AsyncHttpClient()
        assert client.client is None

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager functionality."""
        client = AsyncHttpClient()
        assert client.client is None
        
        async with client:
            assert client.client is not None
            assert isinstance(client.client, httpx.AsyncClient)
        
        # Client should be closed after context
        assert client.client is None

    @pytest.mark.asyncio
    async def test_async_request_success(self):
        """Test successful async HTTP request."""
        async with AsyncHttpClient() as client:
            # Mock the httpx async client
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.text = '{"result": "success"}'
            
            # Create async mock
            async def mock_request(*args, **kwargs):
                return mock_response
            
            client.client.request = mock_request
            
            result = await client.request("GET", "https://example.com")
            
            assert result["status"] == 200
            assert result["headers"]["Content-Type"] == "application/json"
            assert result["body"] == '{"result": "success"}'

    @pytest.mark.asyncio
    async def test_async_request_without_context(self):
        """Test async request without context manager."""
        client = AsyncHttpClient()
        
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await client.request("GET", "https://example.com")

    @pytest.mark.asyncio
    async def test_async_request_with_kwargs(self):
        """Test async request with additional kwargs."""
        async with AsyncHttpClient() as client:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.headers = {"Location": "https://example.com/resource/1"}
            mock_response.text = '{"id": 1}'
            
            # Create async mock
            async def mock_request(*args, **kwargs):
                return mock_response
            
            client.client.request = mock_request
            
            result = await client.request(
                "POST", 
                "https://example.com",
                json={"name": "test"},
                headers={"Authorization": "Bearer token"}
            )
            
            assert result["status"] == 201
            assert result["headers"]["Location"] == "https://example.com/resource/1"
            assert result["body"] == '{"id": 1}'

    @pytest.mark.asyncio
    async def test_async_request_error_handling(self):
        """Test async request error handling."""
        async with AsyncHttpClient() as client:
            # Mock httpx to raise an exception
            client.client.request = Mock(side_effect=httpx.RequestError("Network error"))
            
            with pytest.raises(httpx.RequestError):
                await client.request("GET", "https://example.com")


class TestClientImports:
    """Test client imports."""
    
    def test_client_imports(self):
        """Test client imports."""
        from talkie.core import HttpClient, AsyncHttpClient
        assert HttpClient is not None
        assert AsyncHttpClient is not None

    def test_client_module_imports(self):
        """Test client module imports."""
        from talkie.core.client import HttpClient
        from talkie.core.async_client import AsyncHttpClient
        
        assert HttpClient is not None
        assert AsyncHttpClient is not None
