"""Tests for logger module."""

import logging
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock
import pytest
from talkie.utils.logger import setup_logging, get_logger, log_request, log_response, log_error


class TestSetupLogging:
    """Test logging setup."""
    
    def test_setup_logging_default(self):
        """Test default logging setup."""
        setup_logging()
        
        logger = logging.getLogger("talkie")
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 0  # No handlers by default

    def test_setup_logging_verbose(self):
        """Test logging setup with verbose output."""
        setup_logging(verbose=True)
        
        logger = logging.getLogger("talkie")
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1  # Console handler added

    def test_setup_logging_with_file(self):
        """Test logging setup with file output."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            setup_logging(log_file=temp_path)
            
            logger = logging.getLogger("talkie")
            assert logger.level == logging.INFO
            assert len(logger.handlers) == 1  # File handler added
            
            # Check that file exists
            assert os.path.exists(temp_path)
        finally:
            # Close all handlers to release file handles
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except PermissionError:
                    pass  # File might be locked, ignore

    def test_setup_logging_verbose_and_file(self):
        """Test logging setup with both verbose and file output."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            setup_logging(verbose=True, log_file=temp_path)
            
            logger = logging.getLogger("talkie")
            assert logger.level == logging.INFO
            assert len(logger.handlers) == 2  # Both console and file handlers
            
            # Check that file exists
            assert os.path.exists(temp_path)
        finally:
            # Close all handlers to release file handles
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except PermissionError:
                    pass  # File might be locked, ignore

    def test_setup_logging_different_levels(self):
        """Test logging setup with different levels."""
        for level in [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]:
            setup_logging(level=level)
            logger = logging.getLogger("talkie")
            assert logger.level == level

    def test_setup_logging_clears_handlers(self):
        """Test that setup_logging clears existing handlers."""
        # Add a handler first
        logger = logging.getLogger("talkie")
        handler = logging.StreamHandler()
        logger.addHandler(handler)
        assert len(logger.handlers) == 1
        
        # Setup logging should clear handlers
        setup_logging()
        assert len(logger.handlers) == 0


class TestGetLogger:
    """Test logger retrieval."""
    
    def test_get_logger(self):
        """Test getting logger instance."""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "talkie"

    def test_get_logger_same_instance(self):
        """Test that get_logger returns same instance."""
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2


class TestLogRequest:
    """Test request logging."""

    def test_log_request_basic(self):
        """Test basic request logging."""
        with patch('talkie.utils.logger.logger') as mock_logger:
            log_request("GET", "https://example.com", headers={})
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0]
            assert call_args[1] == "GET"
            assert call_args[2] == "https://example.com"

    def test_log_request_with_headers(self):
        """Test request logging with headers."""
        with patch('talkie.utils.logger.logger') as mock_logger:
            headers = {"Authorization": "Bearer token", "Content-Type": "application/json"}
            log_request("POST", "https://example.com", headers=headers)
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0]
            assert call_args[1] == "POST"
            assert call_args[2] == "https://example.com"

    def test_log_request_with_body(self):
        """Test request logging with data (body)."""
        with patch('talkie.utils.logger.logger') as mock_logger:
            data = {"name": "test"}
            log_request("POST", "https://example.com", headers={}, data=data)
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0]
            assert call_args[1] == "POST"
            assert call_args[2] == "https://example.com"

    def test_log_request_with_all_params(self):
        """Test request logging with all parameters."""
        with patch('talkie.utils.logger.logger') as mock_logger:
            headers = {"Content-Type": "application/json"}
            data = {"name": "test"}
            log_request("POST", "https://example.com", headers=headers, data=data)
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0]
            assert call_args[1] == "POST"
            assert call_args[2] == "https://example.com"


class TestLogResponse:
    """Test response logging."""

    def test_log_response_basic(self):
        """Test basic response logging."""
        with patch('talkie.utils.logger.logger') as mock_logger:
            log_response(200, {}, 1024)
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0]
            assert call_args[1] == 200

    def test_log_response_with_headers(self):
        """Test response logging with headers."""
        with patch('talkie.utils.logger.logger') as mock_logger:
            headers = {"Content-Type": "application/json", "X-Custom": "value"}
            log_response(200, headers, 2048)
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0]
            assert call_args[1] == 200

    def test_log_response_error_status(self):
        """Test response logging with error status."""
        with patch('talkie.utils.logger.logger') as mock_logger:
            log_response(404, {}, 0)
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0]
            assert call_args[1] == 404


class TestLogError:
    """Test error logging."""

    def test_log_error_basic(self):
        """Test basic error logging."""
        with patch('talkie.utils.logger.logger') as mock_logger:
            log_error("Test error")
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "Test error" in call_args

    def test_log_error_with_message(self):
        """Test error logging with custom message."""
        with patch('talkie.utils.logger.logger') as mock_logger:
            error = Exception("Test error")
            log_error("Custom error message", exception=error)
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "Custom error message" in call_args
            assert "Test error" in call_args

    def test_log_error_with_exception(self):
        """Test error logging with exception."""
        with patch('talkie.utils.logger.logger') as mock_logger:
            error = Exception("Test error")
            log_error("Request failed", exception=error)
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "Request failed" in call_args
            assert "Test error" in call_args

    def test_log_error_different_types(self):
        """Test error logging with different error types."""
        with patch('talkie.utils.logger.logger') as mock_logger:
            # Test with ValueError
            error = ValueError("Invalid value")
            log_error("Validation failed", exception=error)
            mock_logger.error.assert_called()

            # Test with RuntimeError
            mock_logger.reset_mock()
            error = RuntimeError("Runtime error")
            log_error("Runtime failed", exception=error)
            mock_logger.error.assert_called()


class TestLoggingIntegration:
    """Test logging integration."""
    
    def test_logging_workflow(self):
        """Test complete logging workflow."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Setup logging
            setup_logging(verbose=True, log_file=temp_path)
            logger = get_logger()
            
            # Test that logger is properly configured
            assert logger.name == "talkie"
            assert logger.level == logging.INFO
            
            # Test logging different types of messages
            log_request("GET", "https://example.com", headers={})
            log_response(200, {}, 1024)
            log_error("Test error", exception=Exception("Test error"))
            
            # Check that log file was created and has content
            assert os.path.exists(temp_path)
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "GET" in content
                assert "200" in content
                assert "Test error" in content
                
        finally:
            # Close all handlers to release file handles
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except PermissionError:
                    pass  # File might be locked, ignore
