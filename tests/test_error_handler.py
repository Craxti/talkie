"""Tests for error handler."""

import pytest
from unittest.mock import MagicMock
from talkie.utils.error_handler import (
    ErrorHandler,
    ErrorContext,
    ErrorInfo,
    ErrorSeverity,
    ValidationError,
    RetryableError,
    NonRetryableError,
    get_error_handler,
    handle_error,
    should_retry,
    validate_url,
    validate_headers,
    validate_timeout,
    validate_concurrency
)


class TestErrorSeverity:
    """Test error severity enum."""

    def test_error_severity_values(self):
        """Test error severity values."""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"


class TestErrorContext:
    """Test error context."""

    def test_error_context_creation(self):
        """Test error context creation."""
        context = ErrorContext(
            operation="test_operation",
            component="test_component",
            user_id="user123",
            request_id="req456"
        )

        assert context.operation == "test_operation"
        assert context.component == "test_component"
        assert context.user_id == "user123"
        assert context.request_id == "req456"
        assert context.additional_data is None


class TestErrorInfo:
    """Test error info."""

    def test_error_info_creation(self):
        """Test error info creation."""
        context = ErrorContext("test", "test")
        error_info = ErrorInfo(
            error_type="TestError",
            message="Test error message",
            severity=ErrorSeverity.MEDIUM,
            context=context
        )

        assert error_info.error_type == "TestError"
        assert error_info.message == "Test error message"
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.context == context
        assert error_info.exception is None
        assert error_info.stack_trace is None
        assert error_info.timestamp > 0
        assert error_info.retry_count == 0
        assert error_info.max_retries == 3


class TestErrorHandler:
    """Test error handler."""

    def test_error_handler_creation(self):
        """Test error handler creation."""
        handler = ErrorHandler()

        assert isinstance(handler.error_callbacks, list)
        assert isinstance(handler.retry_strategies, dict)
        assert len(handler.error_callbacks) == 0

    def test_callback_management(self):
        """Test callback management."""
        handler = ErrorHandler()

        # Test callback
        callback_called = []
        def test_callback(error_info):
            callback_called.append(error_info)

        # Add callback
        handler.add_error_callback(test_callback)
        assert test_callback in handler.error_callbacks

        # Remove callback
        handler.remove_error_callback(test_callback)
        assert test_callback not in handler.error_callbacks

    def test_retry_strategy_management(self):
        """Test retry strategy management."""
        handler = ErrorHandler()

        def test_strategy(error_info):
            return True

        # Add retry strategy
        handler.add_retry_strategy(ValueError, test_strategy)
        assert ValueError in handler.retry_strategies
        assert handler.retry_strategies[ValueError] == test_strategy

    def test_handle_error(self):
        """Test error handling."""
        handler = ErrorHandler()
        context = ErrorContext("test", "test")
        error = ValueError("Test error")

        error_info = handler.handle_error(error, context, ErrorSeverity.MEDIUM)

        assert isinstance(error_info, ErrorInfo)
        assert error_info.error_type == "ValueError"
        assert error_info.message == "Test error"
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.context == context
        assert error_info.exception == error

    def test_should_retry(self):
        """Test retry logic."""
        handler = ErrorHandler()
        context = ErrorContext("test", "test")

        # Test with retry count under limit
        error_info = ErrorInfo(
            error_type="TestError",
            message="Test",
            severity=ErrorSeverity.MEDIUM,
            context=context,
            retry_count=1,
            max_retries=3
        )

        # Should retry for medium severity
        assert handler.should_retry(error_info) == True

        # Test with retry count at limit
        error_info.retry_count = 3
        assert handler.should_retry(error_info) == False

        # Test critical severity
        error_info.severity = ErrorSeverity.CRITICAL
        error_info.retry_count = 1
        assert handler.should_retry(error_info) == False


class TestValidationFunctions:
    """Test validation functions."""

    def test_validate_url(self):
        """Test URL validation."""
        # Valid URLs
        validate_url("http://example.com")
        validate_url("https://example.com")
        validate_url("https://example.com/path")

        # Invalid URLs
        with pytest.raises(ValidationError, match="URL cannot be empty"):
            validate_url("")

        with pytest.raises(ValidationError, match="URL must start with http:// or https://"):
            validate_url("ftp://example.com")

        with pytest.raises(ValidationError, match="Invalid URL format"):
            validate_url("not-a-url")

    def test_validate_headers(self):
        """Test header validation."""
        # Valid headers
        validate_headers({"Content-Type": "application/json"})
        validate_headers(None)

        # Invalid headers
        with pytest.raises(ValidationError, match="Header keys and values must be strings"):
            validate_headers({"Content-Type": 123})

        with pytest.raises(ValidationError, match="Header keys cannot be empty"):
            validate_headers({"": "value"})

        with pytest.raises(ValidationError, match="Invalid characters in header name"):
            validate_headers({"Header\nName": "value"})

    def test_validate_timeout(self):
        """Test timeout validation."""
        # Valid timeouts
        validate_timeout(30)
        validate_timeout(30.5)

        # Invalid timeouts
        with pytest.raises(ValidationError, match="Timeout must be a number"):
            validate_timeout("30")

        with pytest.raises(ValidationError, match="Timeout must be positive"):
            validate_timeout(0)

        with pytest.raises(ValidationError, match="Timeout must be positive"):
            validate_timeout(-1)

        with pytest.raises(ValidationError, match="Timeout cannot exceed 300 seconds"):
            validate_timeout(301)

    def test_validate_concurrency(self):
        """Test concurrency validation."""
        # Valid concurrency
        validate_concurrency(10)
        validate_concurrency(1)

        # Invalid concurrency
        with pytest.raises(ValidationError, match="Concurrency must be an integer"):
            validate_concurrency("10")

        with pytest.raises(ValidationError, match="Concurrency must be positive"):
            validate_concurrency(0)

        with pytest.raises(ValidationError, match="Concurrency must be positive"):
            validate_concurrency(-1)

        with pytest.raises(ValidationError, match="Concurrency cannot exceed 1000"):
            validate_concurrency(1001)


class TestGlobalErrorHandler:
    """Test global error handler functions."""

    def test_get_error_handler(self):
        """Test getting global error handler."""
        handler = get_error_handler()
        assert isinstance(handler, ErrorHandler)

    def test_handle_error_global(self):
        """Test global error handling."""
        context = ErrorContext("test", "test")
        error = ValueError("Test error")

        error_info = handle_error(error, context, ErrorSeverity.MEDIUM)
        assert isinstance(error_info, ErrorInfo)

    def test_should_retry_global(self):
        """Test global retry logic."""
        context = ErrorContext("test", "test")
        error_info = ErrorInfo(
            error_type="TestError",
            message="Test",
            severity=ErrorSeverity.MEDIUM,
            context=context,
            retry_count=1,
            max_retries=3
        )

        result = should_retry(error_info)
        assert isinstance(result, bool)


class TestCustomExceptions:
    """Test custom exceptions."""

    def test_validation_error(self):
        """Test validation error."""
        error = ValidationError("Test validation error")
        assert str(error) == "Test validation error"
        assert isinstance(error, Exception)

    def test_retryable_error(self):
        """Test retryable error."""
        error = RetryableError("Test retryable error")
        assert str(error) == "Test retryable error"
        assert isinstance(error, Exception)

    def test_non_retryable_error(self):
        """Test non-retryable error."""
        error = NonRetryableError("Test non-retryable error")
        assert str(error) == "Test non-retryable error"
        assert isinstance(error, Exception)
