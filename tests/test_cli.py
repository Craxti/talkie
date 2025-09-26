"""Tests for CLI module."""

import pytest
from unittest.mock import patch, Mock
from io import StringIO
import sys
from talkie.cli.main import main
from talkie.cli.output import print_response


class TestMainFunction:
    """Test main CLI function."""
    
    def test_main_function_exists(self):
        """Test that main function exists and is callable."""
        assert callable(main)

    @patch('sys.argv', ['talkie', '--help'])
    @patch('sys.exit')
    def test_main_with_help(self, mock_exit):
        """Test main function with help argument."""
        try:
            main()
        except SystemExit:
            pass  # Expected for help
        # Should not raise any other exceptions

    @patch('sys.argv', ['talkie', 'get', 'https://example.com'])
    @patch('talkie.core.client.HttpClient')
    def test_main_with_get_request(self, mock_client_class):
        """Test main function with GET request."""
        # Mock the client and its context manager
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"result": "success"}'
        
        mock_client.request.return_value = {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body": '{"result": "success"}'
        }
        
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client_class.return_value.__exit__.return_value = None
        
        # Should not raise any exceptions
        try:
            main()
        except SystemExit:
            pass  # Expected for CLI


class TestPrintResponse:
    """Test print response function."""
    
    def test_print_response_basic(self):
        """Test basic print response functionality."""
        response_data = {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body": "Hello World"
        }
        
        # Capture stdout
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            print_response(response_data)
            output = mock_stdout.getvalue()
            
            assert "Response received:" in output
            assert "Status: 200" in output
            assert "Content-Type" in output
            assert "Hello World" in output

    def test_print_response_missing_fields(self):
        """Test print response with missing fields."""
        response_data = {}
        
        # Should not raise exception
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            print_response(response_data)
            output = mock_stdout.getvalue()
            
            assert "Response received:" in output
            assert "Status: Unknown" in output

    def test_print_response_complex_data(self):
        """Test print response with complex data."""
        response_data = {
            "status": 404,
            "headers": {
                "Content-Type": "application/json",
                "X-Custom-Header": "test-value"
            },
            "body": '{"error": "Not Found", "code": 404}'
        }
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            print_response(response_data)
            output = mock_stdout.getvalue()
            
            assert "Status: 404" in output
            assert "Content-Type" in output
            assert "X-Custom-Header" in output
            assert "test-value" in output
            assert "Not Found" in output

    def test_print_response_empty_headers(self):
        """Test print response with empty headers."""
        response_data = {
            "status": 200,
            "headers": {},
            "body": "Success"
        }
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            print_response(response_data)
            output = mock_stdout.getvalue()
            
            assert "Status: 200" in output
            assert "Success" in output

    def test_print_response_none_values(self):
        """Test print response with None values."""
        response_data = {
            "status": None,
            "headers": None,
            "body": None
        }
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            print_response(response_data)
            output = mock_stdout.getvalue()
            
            assert "Response received:" in output
            # Should handle None values gracefully


class TestCLIImports:
    """Test CLI module imports."""
    
    def test_cli_imports(self):
        """Test CLI module imports."""
        from talkie.cli import main as cli_main
        from talkie.cli import output
        
        assert cli_main is not None
        assert output is not None

    def test_cli_main_import(self):
        """Test CLI main import."""
        from talkie.cli.main import main
        assert callable(main)

    def test_cli_output_import(self):
        """Test CLI output import."""
        from talkie.cli.output import print_response
        assert callable(print_response)

    def test_cli_module_structure(self):
        """Test CLI module structure."""
        import talkie.cli
        assert hasattr(talkie.cli, 'main')
        assert hasattr(talkie.cli, 'output')
