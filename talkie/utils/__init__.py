"""Utility modules for Talkie."""

from .config import Config, Environment
from .formatter import (
    DataFormatter, format_json, format_xml, format_html
)
from .colors import get_status_color, get_content_type_color
from .cache import ResponseCache, CacheConfig, CacheEntry
from .logger import Logger
from .error_handler import ErrorHandler
from .validators import validate_url, validate_json
from .memory_manager import MemoryManager
from .performance_config import PerformanceConfig
# from .benchmarks import benchmark_request, benchmark_requests
# Functions not implemented yet
from .curl_generator import generate_curl_command
from .graphql import GraphQLClient, GraphQLResponse
from .history import HistoryManager
from .openapi import OpenAPIClient
from .openapi_generator import OpenApiClientGenerator

__all__ = [
    "Config",
    "Environment",
    "DataFormatter",
    "format_json",
    "format_xml",
    "format_html",
    "get_status_color",
    "get_content_type_color",
    "ResponseCache",
    "CacheConfig",
    "CacheEntry",
    "Logger",
    "ErrorHandler",
    "validate_url",
    "validate_json",
    "MemoryManager",
    "PerformanceConfig",
    # "benchmark_request",
    # "benchmark_requests",
    "generate_curl_command",
    "GraphQLClient",
    "GraphQLResponse",
    "HistoryManager",
    "OpenAPIClient",
    "OpenApiClientGenerator"
]
