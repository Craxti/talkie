"""Logging module for Talkie."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

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
def log_request(method: str, url: str, headers: dict, data: Optional[dict] = None) -> None:
    """Log HTTP request.
    
    Args:
        method: HTTP method
        url: URL address
        headers: Request headers
        data: Request data (for POST, PUT etc.)
    """
    logger.info(f"Sending {method} request: {url}")
    logger.debug(f"Request headers: {headers}")
    
    if data:
        logger.debug(f"Request data: {data}")


def log_response(status_code: int, headers: dict, body_size: int) -> None:
    """Log HTTP response.
    
    Args:
        status_code: Response status code
        headers: Response headers
        body_size: Response body size in bytes
    """
    logger.info(f"Received response with status: {status_code}")
    logger.debug(f"Response headers: {headers}")
    logger.debug(f"Response body size: {body_size} bytes")


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
    
    def log_request(self, method: str, url: str, headers: dict, data: Optional[dict] = None) -> None:
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