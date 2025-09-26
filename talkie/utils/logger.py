"""Enhanced logging module for Talkie."""

import logging
import logging.handlers
import os
import sys
import json
import threading
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
import uuid
from contextlib import contextmanager

# Configure base logger
logger = logging.getLogger("talkie")


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    verbose: bool = False,
) -> None:
    """Configure logging.

    Args:
        level: Logging level
        log_file: Path to log file
        verbose: Flag for console output
    """
    # Set logging level
    logger.setLevel(level)

    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Formatting
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Add console handler if output needed
    if verbose:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Add file handler if path specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def get_default_log_file() -> str:
    """Get default log file path.

    Returns:
        str: Path to log file
    """
    log_dir = os.environ.get(
        "TALKIE_LOG_DIR",
        os.path.expanduser("~/.talkie/logs")
    )

    # Create directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Form filename with current date
    log_file = f"talkie_{datetime.now().strftime('%Y%m%d')}.log"

    return os.path.join(log_dir, log_file)


# Request logs
def log_request(method: str, url: str, headers: dict,
                data: Optional[dict] = None) -> None:
    """Log HTTP request.

    Args:
        method: HTTP method
        url: URL address
        headers: Request headers
        data: Request data (for POST, PUT etc.)
    """
    logger.info("Sending %s request: %s", method, url)
    logger.debug("Request headers: %s", headers)

    if data:
        logger.debug("Request data: %s", data)


def log_response(status_code: int, headers: dict, body_size: int) -> None:
    """Log HTTP response.

    Args:
        status_code: Response status code
        headers: Response headers
        body_size: Response body size in bytes
    """
    logger.info("Received response with status: %s", status_code)
    logger.debug("Response headers: %s", headers)
    logger.debug("Response body size: %s bytes", body_size)


def log_error(message: str, exception: Optional[Exception] = None) -> None:
    """Log an error.

    Args:
        message: Error message
        exception: Exception object, if any
    """
    if exception:
        logger.error(f"{message}: {str(exception)}", exc_info=True)
    else:
        logger.error(message)


class Logger:
    """Logger class for Talkie."""

    def __init__(self) -> None:
        """Initialize logger."""
        self.logger = logger

    def setup(
        self,
        level: int = logging.INFO,
        log_file: Optional[str] = None,
        verbose: bool = False,
    ) -> None:
        """Configure logging.

        Args:
            level: Logging level
            log_file: Path to log file
            verbose: Flag for console output
        """
        setup_logging(level, log_file, verbose)

    def log_request(self, method: str, url: str, headers: dict,
                   data: Optional[dict] = None) -> None:
        """Log HTTP request."""
        log_request(method, url, headers, data)

    def log_response(self, status_code: int, headers: dict, body_size: int) -> None:
        """Log HTTP response."""
        log_response(status_code, headers, body_size)

    def log_error(self, message: str, exception: Optional[Exception] = None) -> None:
        """Log an error."""
        log_error(message, exception)

    def info(self, message: str) -> None:
        """Log an information message."""
        self.logger.info(message)

    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(message)

    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)

    def error(self, message: str, exc_info: bool = False) -> None:
        """Log an error message."""
        self.logger.error(message, exc_info=exc_info)


class StructuredLogger:
    """Enhanced structured logger with context and performance tracking."""

    def __init__(self, name: str = "talkie"):
        self.logger = logging.getLogger(name)
        self.context = threading.local()
        self._setup_default_handlers()

        # Performance tracking
        self.performance_data = []
        self.request_counters = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }

    def _setup_default_handlers(self):
        """Setup default handlers if none exist."""
        if not self.logger.handlers:
            # Console handler for warnings and errors
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(logging.WARNING)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

            # File handler for all logs
            try:
                log_file = get_default_log_file()
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file, maxBytes=10*1024*1024, backupCount=5  # 10MB files, keep 5
                )
                file_handler.setLevel(logging.DEBUG)
                file_formatter = JsonFormatter()
                file_handler.setFormatter(file_formatter)
                self.logger.addHandler(file_handler)
            except Exception:
                pass  # If file logging fails, continue with console only

            self.logger.setLevel(logging.DEBUG)

    def set_context(self, **kwargs):
        """Set logging context for current thread."""
        if not hasattr(self.context, 'data'):
            self.context.data = {}
        self.context.data.update(kwargs)

    def clear_context(self):
        """Clear logging context for current thread."""
        if hasattr(self.context, 'data'):
            self.context.data.clear()

    def get_context(self) -> Dict[str, Any]:
        """Get current logging context."""
        if hasattr(self.context, 'data'):
            return self.context.data.copy()
        return {}

    @contextmanager
    def context_manager(self, **kwargs):
        """Context manager for temporary logging context."""
        old_context = self.get_context()
        try:
            self.set_context(**kwargs)
            yield
        finally:
            self.clear_context()
            self.set_context(**old_context)

    def _log_with_context(self, level: int, message: str,
                         extra_data: Optional[Dict[str, Any]] = None):
        """Log message with context."""
        context = self.get_context()

        log_data = {
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "context": context
        }

        if extra_data:
            log_data.update(extra_data)

        # Create log record
        record = logging.LogRecord(
            name=self.logger.name,
            level=level,
            pathname="",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )

        # Add structured data to record
        record.structured_data = log_data

        self.logger.handle(record)

    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, message, kwargs)

    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self._log_with_context(logging.INFO, message, kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, message, kwargs)

    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message with context and exception details."""
        extra_data = kwargs.copy()

        if exception:
            extra_data.update({
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "traceback": traceback.format_exc()
            })

        self._log_with_context(logging.ERROR, message, extra_data)

    def log_request(self, method: str, url: str, headers: Optional[Dict] = None,
                   data: Optional[Any] = None, request_id: Optional[str] = None):
        """Log HTTP request with detailed information."""
        if not request_id:
            request_id = str(uuid.uuid4())[:8]

        self.request_counters["total_requests"] += 1

        request_data = {
            "request_id": request_id,
            "method": method,
            "url": url,
            "has_headers": bool(headers),
            "has_data": bool(data),
            "event_type": "http_request"
        }

        # Don't log sensitive headers
        if headers:
            safe_headers = {k: v for k, v in headers.items()
                          if k.lower() not in ['authorization', 'cookie', 'x-api-key']}
            request_data["headers"] = safe_headers

        with self.context_manager(request_id=request_id):
            self.info(f"HTTP {method} request to {url}", **request_data)

    def log_response(self, status_code: int, headers: Optional[Dict] = None,
                    body_size: Optional[int] = None, duration: Optional[float] = None,
                    request_id: Optional[str] = None, from_cache: bool = False):
        """Log HTTP response with detailed information."""
        if 200 <= status_code < 300:
            self.request_counters["successful_requests"] += 1
        else:
            self.request_counters["failed_requests"] += 1

        if from_cache:
            self.request_counters["cache_hits"] += 1
        else:
            self.request_counters["cache_misses"] += 1

        response_data = {
            "request_id": request_id,
            "status_code": status_code,
            "body_size_bytes": body_size,
            "duration_ms": duration * 1000 if duration else None,
            "from_cache": from_cache,
            "event_type": "http_response"
        }

        # Track performance data
        if duration:
            self.performance_data.append({
                "timestamp": datetime.utcnow().isoformat(),
                "duration": duration,
                "status_code": status_code,
                "from_cache": from_cache
            })

            # Keep only last 1000 entries
            if len(self.performance_data) > 1000:
                self.performance_data = self.performance_data[-1000:]

        context = {"request_id": request_id} if request_id else {}
        with self.context_manager(**context):
            level = logging.INFO if 200 <= status_code < 300 else logging.WARNING
            self._log_with_context(
                level,
                (f"HTTP response {status_code} ({duration:.3f}s)"
                 if duration else f"HTTP response {status_code}"),
                response_data
            )

    def log_cache_operation(self, operation: str, key: str, hit: bool = False,
                          size: Optional[int] = None):
        """Log cache operations."""
        cache_data = {
            "operation": operation,
            "cache_key": (key[:50] + "..." if len(key) > 50 else key),
            "cache_hit": hit,
            "size_bytes": size,
            "event_type": "cache_operation"
        }

        self.debug(f"Cache {operation}: {'HIT' if hit else 'MISS'}", **cache_data)

    def log_performance_metric(self, metric_name: str, value: float, unit: str = "ms"):
        """Log performance metric."""
        perf_data = {
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "event_type": "performance_metric"
        }

        self.info(f"Performance: {metric_name} = {value}{unit}", **perf_data)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.performance_data:
            return {}

        durations = [p["duration"] for p in self.performance_data]

        return {
            "request_counters": self.request_counters.copy(),
            "response_times": {
                "count": len(durations),
                "avg": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations),
                "p95": sorted(durations)[int(len(durations) * 0.95)] if durations else 0
            },
            "cache_efficiency": {
                "hit_rate": (self.request_counters["cache_hits"] /
                            max(1, self.request_counters["cache_hits"] +
                                self.request_counters["cache_misses"]) * 100)
            }
        }

    def export_logs(self, output_file: str, level: str = "INFO") -> int:
        """Export logs to file in structured format."""
        # level_num = getattr(logging, level.upper())  # Not used currently
        count = 0

        # This is a simplified export - in practice you'd read from log files
        summary = self.get_performance_summary()

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "export_timestamp": datetime.utcnow().isoformat(),
                "performance_summary": summary,
                "note": "Full log export requires access to log files"
            }, f, indent=2)
            count = 1

        return count


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add structured data if available
        if hasattr(record, 'structured_data'):
            log_data.update(record.structured_data)

        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


# Global structured logger instance
structured_logger = StructuredLogger()


def get_structured_logger() -> StructuredLogger:
    """Get global structured logger instance."""
    return structured_logger


def setup_debug_logging(enable_debug: bool = True, log_file: Optional[str] = None):
    """Setup debug logging configuration."""
    level = logging.DEBUG if enable_debug else logging.INFO

    # Configure main logger
    setup_logging(level, log_file, verbose=enable_debug)

    # Configure structured logger
    if enable_debug:
        structured_logger.logger.setLevel(logging.DEBUG)

        # Add more detailed console output for debug
        debug_handler = logging.StreamHandler(sys.stdout)
        debug_handler.setLevel(logging.DEBUG)
        debug_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
        )
        debug_handler.setFormatter(debug_formatter)

        # Add to main logger (avoid duplicate logs)
        root_logger = logging.getLogger()
        if not any(isinstance(h, logging.StreamHandler) and h.stream == sys.stdout
                  for h in root_logger.handlers):
            root_logger.addHandler(debug_handler)
            root_logger.setLevel(logging.DEBUG)


# Convenience functions for direct import
def get_logger():
    """Get logger instance."""
    return logger
