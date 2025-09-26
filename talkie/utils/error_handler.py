"""Enhanced error handling and validation utilities."""

import traceback
from typing import Any, Dict, Optional, Union, Callable, Type
from dataclasses import dataclass
from enum import Enum
from ..utils.logger import Logger

logger = Logger()


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Context information for errors."""
    operation: str
    component: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class ErrorInfo:
    """Structured error information."""
    error_type: str
    message: str
    severity: ErrorSeverity
    context: ErrorContext
    exception: Optional[Exception] = None
    stack_trace: Optional[str] = None
    timestamp: float = 0.0
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        import time
        if self.timestamp == 0.0:
            self.timestamp = time.time()
        if self.stack_trace is None and self.exception:
            self.stack_trace = traceback.format_exc()


class ErrorHandler:
    """Enhanced error handling and recovery."""

    def __init__(self):
        self.error_callbacks: list[Callable[[ErrorInfo], None]] = []
        self.retry_strategies: Dict[Type[Exception], Callable[[ErrorInfo], bool]] = {}
        self._setup_default_retry_strategies()

    def add_error_callback(self, callback: Callable[[ErrorInfo], None]) -> None:
        """Add error callback."""
        self.error_callbacks.append(callback)

    def remove_error_callback(self, callback: Callable[[ErrorInfo], None]) -> None:
        """Remove error callback."""
        if callback in self.error_callbacks:
            self.error_callbacks.remove(callback)

    def add_retry_strategy(self, exception_type: Type[Exception],
                          strategy: Callable[[ErrorInfo], bool]) -> None:
        """Add retry strategy for specific exception type."""
        self.retry_strategies[exception_type] = strategy

    def handle_error(self, error: Exception, context: ErrorContext,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> ErrorInfo:
        """Handle and process error."""
        error_info = ErrorInfo(
            error_type=type(error).__name__,
            message=str(error),
            severity=severity,
            context=context,
            exception=error
        )

        # Log error
        self._log_error(error_info)

        # Call callbacks
        for callback in self.error_callbacks:
            try:
                callback(error_info)
            except Exception:
                pass  # Ignore callback errors

        return error_info

    def should_retry(self, error_info: ErrorInfo) -> bool:
        """Determine if operation should be retried."""
        if error_info.retry_count >= error_info.max_retries:
            return False

        exception_type = type(error_info.exception) if error_info.exception else None
        if exception_type in self.retry_strategies:
            return self.retry_strategies[exception_type](error_info)

        # Default retry logic
        return self._default_retry_logic(error_info)

    def _setup_default_retry_strategies(self) -> None:
        """Setup default retry strategies."""
        # HTTP timeout errors - retry
        try:
            import httpx
            self.add_retry_strategy(
                httpx.TimeoutException,
                lambda e: e.retry_count < 2
            )

            # HTTP connection errors - retry
            self.add_retry_strategy(
                httpx.ConnectError,
                lambda e: e.retry_count < 3
            )

            # HTTP status errors - retry for 5xx
            self.add_retry_strategy(
                httpx.HTTPStatusError,
                lambda e: (
                    e.exception and
                    hasattr(e.exception, 'response') and
                    e.exception.response.status_code >= 500 and
                    e.retry_count < 2
                )
            )
        except ImportError:
            pass  # httpx not available

    def _default_retry_logic(self, error_info: ErrorInfo) -> bool:
        """Default retry logic."""
        # Don't retry critical errors
        if error_info.severity == ErrorSeverity.CRITICAL:
            return False

        # Retry network-related errors
        network_errors = ['TimeoutException', 'ConnectError', 'NetworkError']
        if error_info.error_type in network_errors:
            return error_info.retry_count < 3

        # Don't retry validation errors
        if error_info.error_type in ['ValidationError', 'ValueError', 'TypeError']:
            return False

        # Default: retry up to 2 times for medium/high severity
        return (error_info.severity in [ErrorSeverity.MEDIUM, ErrorSeverity.HIGH] and
                error_info.retry_count < 2)

    def _log_error(self, error_info: ErrorInfo) -> None:
        """Log error information."""
        log_level = {
            ErrorSeverity.LOW: logger.debug,
            ErrorSeverity.MEDIUM: logger.warning,
            ErrorSeverity.HIGH: logger.error,
            ErrorSeverity.CRITICAL: logger.error
        }.get(error_info.severity, logger.error)

        message = (f"[{error_info.context.component}] "
                  f"{error_info.context.operation}: {error_info.message}")
        if error_info.context.request_id:
            message += f" (Request ID: {error_info.context.request_id})"

        log_level(message)

        if (error_info.stack_trace and
            error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]):
            logger.debug(f"Stack trace: {error_info.stack_trace}")


class ValidationError(Exception):
    """Custom validation error."""


class RetryableError(Exception):
    """Error that can be retried."""


class NonRetryableError(Exception):
    """Error that should not be retried."""


def validate_url(url: str) -> None:
    """Validate URL format."""
    if not url:
        raise ValidationError("URL cannot be empty")

    if not url.startswith(('http://', 'https://')):
        raise ValidationError("URL must start with http:// or https://")

    # Basic URL validation
    try:
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        if not parsed.netloc:
            raise ValidationError("Invalid URL format")
    except Exception as e:
        raise ValidationError(f"Invalid URL format: {str(e)}")


def validate_headers(headers: Optional[Dict[str, str]]) -> None:
    """Validate HTTP headers."""
    if headers is None:
        return

    for key, value in headers.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValidationError("Header keys and values must be strings")

        if not key.strip():
            raise ValidationError("Header keys cannot be empty")

        # Check for invalid characters in header names
        if any(char in key for char in ['\r', '\n', '\0']):
            raise ValidationError(f"Invalid characters in header name: {key}")


def validate_timeout(timeout: Union[int, float]) -> None:
    """Validate timeout value."""
    if not isinstance(timeout, (int, float)):
        raise ValidationError("Timeout must be a number")

    if timeout <= 0:
        raise ValidationError("Timeout must be positive")

    if timeout > 300:  # 5 minutes max
        raise ValidationError("Timeout cannot exceed 300 seconds")


def validate_concurrency(concurrency: int) -> None:
    """Validate concurrency value."""
    if not isinstance(concurrency, int):
        raise ValidationError("Concurrency must be an integer")

    if concurrency <= 0:
        raise ValidationError("Concurrency must be positive")

    if concurrency > 1000:
        raise ValidationError("Concurrency cannot exceed 1000")


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_error(error: Exception, context: ErrorContext,
                severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> ErrorInfo:
    """Handle error using global error handler."""
    handler = get_error_handler()
    return handler.handle_error(error, context, severity)


def should_retry(error_info: ErrorInfo) -> bool:
    """Check if error should be retried."""
    handler = get_error_handler()
    return handler.should_retry(error_info)
