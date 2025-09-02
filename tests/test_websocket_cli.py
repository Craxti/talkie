"""Tests for WebSocket CLI command."""

import pytest
import tempfile
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typer.testing import CliRunner

from talkie.cli.main import cli
from talkie.core.websocket_client import WebSocketMessage


class TestWebSocketCLI:
    """Test cases for WebSocket CLI command."""
    
    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def mock_websocket_client(self):
        """Create mock WebSocket client."""
        with patch('talkie.cli.main.WebSocketClient') as mock:
            client_instance = Mock()
            mock.return_value = client_instance
            
            # Mock async methods
            client_instance.connect = AsyncMock(return_value=True)
            client_instance.disconnect = AsyncMock()
            client_instance.send = AsyncMock(return_value=True)
            client_instance.receive = AsyncMock(return_value=None)
            client_instance.is_connected = True
            
            yield client_instance
    
    def test_websocket_help(self, runner):
        """Test WebSocket command help."""
        result = runner.invoke(cli, ["websocket", "--help"])
        assert result.exit_code == 0
        assert "Connect to WebSocket server" in result.stdout
        assert "--interactive" in result.stdout
        assert "--message" in result.stdout
    
    @patch('asyncio.run')
    def test_websocket_simple_connection(self, mock_asyncio_run, runner, mock_websocket_client):
        """Test simple WebSocket connection."""
        # Mock asyncio.run to avoid actually running async code
        mock_asyncio_run.return_value = None
        
        result = runner.invoke(cli, [
            "websocket",
            "ws://echo.websocket.org"
        ])
        
        assert result.exit_code == 0
        # Verify that asyncio.run was called
        mock_asyncio_run.assert_called_once()
    
    @patch('asyncio.run')
    def test_websocket_with_message(self, mock_asyncio_run, runner, mock_websocket_client):
        """Test WebSocket connection with initial message."""
        mock_asyncio_run.return_value = None
        
        result = runner.invoke(cli, [
            "websocket",
            "ws://echo.websocket.org",
            "--message", "Hello WebSocket"
        ])
        
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()
    
    @patch('asyncio.run')
    def test_websocket_with_headers(self, mock_asyncio_run, runner, mock_websocket_client):
        """Test WebSocket connection with custom headers."""
        mock_asyncio_run.return_value = None
        
        result = runner.invoke(cli, [
            "websocket",
            "ws://echo.websocket.org",
            "--header", "Authorization:Bearer token123",
            "--header", "X-Custom-Header:value"
        ])
        
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()
    
    @patch('asyncio.run')
    def test_websocket_interactive_mode(self, mock_asyncio_run, runner, mock_websocket_client):
        """Test WebSocket interactive mode."""
        mock_asyncio_run.return_value = None
        
        result = runner.invoke(cli, [
            "websocket",
            "ws://echo.websocket.org",
            "--interactive"
        ])
        
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()
    
    @patch('asyncio.run')
    def test_websocket_listen_mode(self, mock_asyncio_run, runner, mock_websocket_client):
        """Test WebSocket listen-only mode."""
        mock_asyncio_run.return_value = None
        
        result = runner.invoke(cli, [
            "websocket",
            "ws://echo.websocket.org",
            "--listen",
            "--duration", "5"
        ])
        
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()
    
    @patch('asyncio.run')
    def test_websocket_with_timeout(self, mock_asyncio_run, runner, mock_websocket_client):
        """Test WebSocket connection with custom timeout."""
        mock_asyncio_run.return_value = None
        
        result = runner.invoke(cli, [
            "websocket",
            "wss://secure.websocket.org",
            "--timeout", "30"
        ])
        
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()
    
    @patch('asyncio.run')
    def test_websocket_with_certificate(self, mock_asyncio_run, runner, mock_websocket_client):
        """Test WebSocket connection with client certificate."""
        # Create temporary certificate file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write("fake certificate content")
            cert_file = f.name
        
        try:
            result = runner.invoke(cli, [
                "websocket",
                "wss://secure.websocket.org",
                "--cert", cert_file
            ])
            
            assert result.exit_code == 0
            mock_asyncio_run.assert_called_once()
        
        finally:
            import os
            os.unlink(cert_file)
    
    @patch('asyncio.run')
    def test_websocket_save_output(self, mock_asyncio_run, runner, mock_websocket_client):
        """Test WebSocket connection with output file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            output_file = f.name
        
        try:
            result = runner.invoke(cli, [
                "websocket",
                "ws://echo.websocket.org",
                "--output", output_file,
                "--max-messages", "1"
            ])
            
            assert result.exit_code == 0
            mock_asyncio_run.assert_called_once()
        
        finally:
            import os
            os.unlink(output_file)
    
    @patch('asyncio.run')
    def test_websocket_max_messages_limit(self, mock_asyncio_run, runner, mock_websocket_client):
        """Test WebSocket connection with message limit."""
        mock_asyncio_run.return_value = None
        
        result = runner.invoke(cli, [
            "websocket",
            "ws://echo.websocket.org",
            "--max-messages", "5"
        ])
        
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()
    
    def test_websocket_invalid_uri(self, runner):
        """Test WebSocket command with invalid URI."""
        result = runner.invoke(cli, [
            "websocket",
            "invalid-uri"
        ])
        
        # Should fail during validation or connection
        assert result.exit_code != 0
    
    @patch('asyncio.run')
    def test_websocket_verbose_output(self, mock_asyncio_run, runner, mock_websocket_client):
        """Test WebSocket connection with verbose output."""
        mock_asyncio_run.return_value = None
        
        result = runner.invoke(cli, [
            "websocket",
            "ws://echo.websocket.org",
            "--verbose",
            "--message", "test"
        ])
        
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()


class TestWebSocketClientAsync:
    """Test actual WebSocket client functionality."""
    
    @pytest.mark.asyncio
    async def test_websocket_client_creation(self):
        """Test WebSocket client creation."""
        from talkie.core.websocket_client import WebSocketClient
        
        client = WebSocketClient("ws://echo.websocket.org")
        
        assert client.uri == "ws://echo.websocket.org"
        assert client.timeout == 10.0
        assert client.auto_reconnect is True
        assert not client.is_connected
    
    @pytest.mark.asyncio
    async def test_websocket_client_with_ssl(self):
        """Test WebSocket client with SSL configuration."""
        from talkie.core.websocket_client import WebSocketClient
        
        # Mock SSL context creation to avoid real certificate validation
        with patch('ssl.create_default_context') as mock_ssl:
            mock_context = Mock()
            mock_ssl.return_value = mock_context
            
            client = WebSocketClient(
                "wss://secure.websocket.org",
                cert_file="/fake/cert.pem",
                key_file="/fake/key.pem"
            )
            
            assert client.ssl_context is not None
            assert client.uri == "wss://secure.websocket.org"
            
            # Verify SSL context was created and configured
            mock_ssl.assert_called_once()
            mock_context.load_cert_chain.assert_called_once_with("/fake/cert.pem", "/fake/key.pem")
    
    @pytest.mark.asyncio
    async def test_websocket_message_creation(self):
        """Test WebSocket message creation."""
        from talkie.core.websocket_client import WebSocketMessage
        
        # Test text message
        msg1 = WebSocketMessage(type="text", data="Hello")
        assert msg1.type == "text"
        assert msg1.data == "Hello"
        
        # Test JSON message
        msg2 = WebSocketMessage(type="json", data={"key": "value"})
        assert msg2.type == "json"
        assert msg2.data == {"key": "value"}
        
        # Test binary message
        msg3 = WebSocketMessage(type="binary", data=b"binary data")
        assert msg3.type == "binary"
        assert msg3.data == b"binary data"
