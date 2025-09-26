"""Performance configuration and optimization settings."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import os


@dataclass
class PerformanceConfig:
    """Configuration for performance optimizations."""

    # HTTP Client settings
    max_connections: int = 100
    max_keepalive_connections: int = 20
    connection_timeout: float = 30.0
    read_timeout: float = 30.0
    enable_http2: bool = True

    # Caching settings
    cache_enabled: bool = True
    cache_max_size_mb: float = 100.0
    cache_max_entries: int = 1000
    cache_ttl_seconds: int = 3600
    cache_max_response_size_mb: float = 1.0

    # Async settings
    max_concurrent_requests: int = 50
    request_delay_ms: float = 0.0
    batch_size: int = 10

    # Memory management
    max_memory_usage_mb: float = 500.0
    gc_threshold: int = 1000
    enable_memory_monitoring: bool = True

    # Logging settings
    log_performance_metrics: bool = True
    log_level: str = "INFO"
    max_log_file_size_mb: float = 10.0
    max_log_files: int = 5

    # Benchmark settings
    benchmark_warmup_requests: int = 10
    benchmark_sample_size: int = 100
    benchmark_timeout_seconds: int = 300

    @classmethod
    def from_env(cls) -> "PerformanceConfig":
        """Create configuration from environment variables."""
        return cls(
            max_connections=int(os.getenv("TALKIE_MAX_CONNECTIONS", "100")),
            max_keepalive_connections=int(os.getenv("TALKIE_MAX_KEEPALIVE", "20")),
            connection_timeout=float(os.getenv("TALKIE_CONNECTION_TIMEOUT", "30.0")),
            read_timeout=float(os.getenv("TALKIE_READ_TIMEOUT", "30.0")),
            enable_http2=os.getenv("TALKIE_HTTP2", "true").lower() == "true",
            cache_enabled=os.getenv("TALKIE_CACHE_ENABLED", "true").lower() == "true",
            cache_max_size_mb=float(os.getenv("TALKIE_CACHE_MAX_SIZE_MB", "100.0")),
            cache_max_entries=int(os.getenv("TALKIE_CACHE_MAX_ENTRIES", "1000")),
            cache_ttl_seconds=int(os.getenv("TALKIE_CACHE_TTL", "3600")),
            cache_max_response_size_mb=float(os.getenv("TALKIE_CACHE_MAX_RESPONSE_SIZE_MB", "1.0")),
            max_concurrent_requests=int(os.getenv("TALKIE_MAX_CONCURRENT", "50")),
            request_delay_ms=float(os.getenv("TALKIE_REQUEST_DELAY_MS", "0.0")),
            batch_size=int(os.getenv("TALKIE_BATCH_SIZE", "10")),
            max_memory_usage_mb=float(os.getenv("TALKIE_MAX_MEMORY_MB", "500.0")),
            gc_threshold=int(os.getenv("TALKIE_GC_THRESHOLD", "1000")),
            enable_memory_monitoring=os.getenv("TALKIE_MEMORY_MONITORING", "true").lower() == "true",
            log_performance_metrics=os.getenv("TALKIE_LOG_PERFORMANCE", "true").lower() == "true",
            log_level=os.getenv("TALKIE_LOG_LEVEL", "INFO"),
            max_log_file_size_mb=float(os.getenv("TALKIE_MAX_LOG_SIZE_MB", "10.0")),
            max_log_files=int(os.getenv("TALKIE_MAX_LOG_FILES", "5")),
            benchmark_warmup_requests=int(os.getenv("TALKIE_BENCHMARK_WARMUP", "10")),
            benchmark_sample_size=int(os.getenv("TALKIE_BENCHMARK_SAMPLE", "100")),
            benchmark_timeout_seconds=int(os.getenv("TALKIE_BENCHMARK_TIMEOUT", "300"))
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "max_connections": self.max_connections,
            "max_keepalive_connections": self.max_keepalive_connections,
            "connection_timeout": self.connection_timeout,
            "read_timeout": self.read_timeout,
            "enable_http2": self.enable_http2,
            "cache_enabled": self.cache_enabled,
            "cache_max_size_mb": self.cache_max_size_mb,
            "cache_max_entries": self.cache_max_entries,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "cache_max_response_size_mb": self.cache_max_response_size_mb,
            "max_concurrent_requests": self.max_concurrent_requests,
            "request_delay_ms": self.request_delay_ms,
            "batch_size": self.batch_size,
            "max_memory_usage_mb": self.max_memory_usage_mb,
            "gc_threshold": self.gc_threshold,
            "enable_memory_monitoring": self.enable_memory_monitoring,
            "log_performance_metrics": self.log_performance_metrics,
            "log_level": self.log_level,
            "max_log_file_size_mb": self.max_log_file_size_mb,
            "max_log_files": self.max_log_files,
            "benchmark_warmup_requests": self.benchmark_warmup_requests,
            "benchmark_sample_size": self.benchmark_sample_size,
            "benchmark_timeout_seconds": self.benchmark_timeout_seconds
        }

    def validate(self) -> None:
        """Validate configuration values."""
        if self.max_connections <= 0:
            raise ValueError("max_connections must be positive")
        if self.max_keepalive_connections <= 0:
            raise ValueError("max_keepalive_connections must be positive")
        if self.connection_timeout <= 0:
            raise ValueError("connection_timeout must be positive")
        if self.read_timeout <= 0:
            raise ValueError("read_timeout must be positive")
        if self.cache_max_size_mb <= 0:
            raise ValueError("cache_max_size_mb must be positive")
        if self.cache_max_entries <= 0:
            raise ValueError("cache_max_entries must be positive")
        if self.cache_ttl_seconds <= 0:
            raise ValueError("cache_ttl_seconds must be positive")
        if self.cache_max_response_size_mb <= 0:
            raise ValueError("cache_max_response_size_mb must be positive")
        if self.max_concurrent_requests <= 0:
            raise ValueError("max_concurrent_requests must be positive")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.max_memory_usage_mb <= 0:
            raise ValueError("max_memory_usage_mb must be positive")
        if self.gc_threshold <= 0:
            raise ValueError("gc_threshold must be positive")
        if self.max_log_file_size_mb <= 0:
            raise ValueError("max_log_file_size_mb must be positive")
        if self.max_log_files <= 0:
            raise ValueError("max_log_files must be positive")
        if self.benchmark_warmup_requests < 0:
            raise ValueError("benchmark_warmup_requests must be non-negative")
        if self.benchmark_sample_size <= 0:
            raise ValueError("benchmark_sample_size must be positive")
        if self.benchmark_timeout_seconds <= 0:
            raise ValueError("benchmark_timeout_seconds must be positive")


# Global performance configuration
_performance_config: Optional[PerformanceConfig] = None


def get_performance_config() -> PerformanceConfig:
    """Get global performance configuration."""
    global _performance_config
    if _performance_config is None:
        _performance_config = PerformanceConfig.from_env()
        _performance_config.validate()
    return _performance_config


def set_performance_config(config: PerformanceConfig) -> None:
    """Set global performance configuration."""
    global _performance_config
    config.validate()
    _performance_config = config


def reset_performance_config() -> None:
    """Reset to default performance configuration."""
    global _performance_config
    _performance_config = None
