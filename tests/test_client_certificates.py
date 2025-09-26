"""Tests for client certificate functionality."""

import pytest
import tempfile
import os
from unittest.mock import patch, Mock
from talkie.core.client import HttpClient


class TestClientCertificates:
    """Test cases for client certificate support."""

    def test_http_client_init_without_cert(self):
        """Test HttpClient initialization without certificates."""
        client = HttpClient()
        assert client.cert is None
        assert client.timeout == 30
        assert client.verify is True
        assert client.follow_redirects is True

    @patch('httpx.Client')
    def test_http_client_init_with_pem_cert(self, mock_httpx_client):
        """Test HttpClient initialization with PEM certificate."""
        # Create temporary certificate file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write("fake certificate content")
            cert_path = f.name

        try:
            client = HttpClient(cert=cert_path)
            assert client.cert == cert_path
        finally:
            os.unlink(cert_path)

    @patch('httpx.Client')
    def test_http_client_init_with_cert_key_tuple(self, mock_httpx_client):
        """Test HttpClient initialization with certificate and key files."""
        # Create temporary certificate and key files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.crt', delete=False) as cert_file:
            cert_file.write("fake certificate content")
            cert_path = cert_file.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.key', delete=False) as key_file:
            key_file.write("fake key content")
            key_path = key_file.name

        try:
            cert_tuple = (cert_path, key_path)
            client = HttpClient(cert=cert_tuple)
            assert client.cert == cert_tuple
        finally:
            os.unlink(cert_path)
            os.unlink(key_path)

    def test_http_client_cert_file_not_found(self):
        """Test HttpClient initialization with non-existent certificate file."""
        with pytest.raises(ValueError, match="Certificate file not found"):
            HttpClient(cert="/path/to/nonexistent/cert.pem")

    def test_http_client_cert_tuple_cert_not_found(self):
        """Test HttpClient initialization with non-existent certificate in tuple."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.key', delete=False) as key_file:
            key_file.write("fake key content")
            key_path = key_file.name

        try:
            with pytest.raises(ValueError, match="Certificate file not found"):
                HttpClient(cert=("/path/to/nonexistent/cert.crt", key_path))
        finally:
            os.unlink(key_path)

    def test_http_client_cert_tuple_key_not_found(self):
        """Test HttpClient initialization with non-existent key in tuple."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.crt', delete=False) as cert_file:
            cert_file.write("fake certificate content")
            cert_path = cert_file.name

        try:
            with pytest.raises(ValueError, match="Key file not found"):
                HttpClient(cert=(cert_path, "/path/to/nonexistent/key.key"))
        finally:
            os.unlink(cert_path)

    def test_http_client_invalid_cert_type(self):
        """Test HttpClient initialization with invalid certificate type."""
        with pytest.raises(ValueError, match="cert must be a string"):
            HttpClient(cert=123)

    def test_http_client_invalid_cert_tuple_length(self):
        """Test HttpClient initialization with invalid certificate tuple length."""
        with pytest.raises(ValueError, match="cert must be a string"):
            HttpClient(cert=("cert", "key", "extra"))

    @patch('os.access')
    @patch('os.path.isfile')
    def test_http_client_cert_not_readable(self, mock_isfile, mock_access):
        """Test HttpClient initialization with non-readable certificate file."""
        mock_isfile.return_value = True
        mock_access.return_value = False

        with pytest.raises(ValueError, match="Certificate file not readable"):
            HttpClient(cert="/path/to/cert.pem")

    @patch('httpx.Client')
    def test_http_client_passes_cert_to_httpx(self, mock_httpx_client):
        """Test that certificate is passed to httpx.Client."""
        # Create temporary certificate file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write("fake certificate content")
            cert_path = f.name

        try:
            client = HttpClient(cert=cert_path)

            # Verify httpx.Client was called with correct parameters
            mock_httpx_client.assert_called_once()
            call_args = mock_httpx_client.call_args
            assert call_args[1]['cert'] == cert_path
            assert call_args[1]['verify'] is True
            assert call_args[1]['follow_redirects'] is True
        finally:
            os.unlink(cert_path)

    def test_validate_cert_files_with_empty_tuple(self):
        """Test certificate validation with empty tuple."""
        client = HttpClient()
        with pytest.raises(ValueError, match="cert must be a string"):
            client._validate_cert_files(())
