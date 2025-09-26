"""Tests for performance configuration."""

import pytest
import os
from talkie.utils.performance_config import (
    PerformanceConfig,
    get_performance_config,
    set_performance_config,
    reset_performance_config
)


class TestPerformanceConfig:
    """Test performance configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PerformanceConfig()

        assert config.max_connections == 100
        assert config.max_keepalive_connections == 20
        assert config.connection_timeout == 30.0
        assert config.read_timeout == 30.0
        assert config.enable_http2 == True
        assert config.cache_enabled == True
        assert config.cache_max_size_mb == 100.0
        assert config.cache_max_entries == 1000
        assert config.cache_ttl_seconds == 3600
        assert config.cache_max_response_size_mb == 1.0
        assert config.max_concurrent_requests == 50
        assert config.request_delay_ms == 0.0
        assert config.batch_size == 10
        assert config.max_memory_usage_mb == 500.0
        assert config.gc_threshold == 1000
        assert config.enable_memory_monitoring == True
        assert config.log_performance_metrics == True
        assert config.log_level == "INFO"
        assert config.max_log_file_size_mb == 10.0
        assert config.max_log_files == 5
        assert config.benchmark_warmup_requests == 10
        assert config.benchmark_sample_size == 100
        assert config.benchmark_timeout_seconds == 300

    def test_from_env(self):
        """Test configuration from environment variables."""
        # Set test environment variables
        os.environ["TALKIE_MAX_CONNECTIONS"] = "200"
        os.environ["TALKIE_CACHE_ENABLED"] = "false"
        os.environ["TALKIE_LOG_LEVEL"] = "DEBUG"

        try:
            config = PerformanceConfig.from_env()

            assert config.max_connections == 200
            assert config.cache_enabled == False
            assert config.log_level == "DEBUG"
        finally:
            # Clean up environment
            for key in ["TALKIE_MAX_CONNECTIONS", "TALKIE_CACHE_ENABLED", "TALKIE_LOG_LEVEL"]:
                if key in os.environ:
                    del os.environ[key]

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = PerformanceConfig()
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert "max_connections" in config_dict
        assert "cache_enabled" in config_dict
        assert "log_level" in config_dict
        assert config_dict["max_connections"] == 100

    def test_validation(self):
        """Test configuration validation."""
        # Test valid configuration
        config = PerformanceConfig()
        config.validate()  # Should not raise

        # Test invalid configurations
        with pytest.raises(ValueError, match="max_connections must be positive"):
            config.max_connections = 0
            config.validate()

        with pytest.raises(ValueError, match="connection_timeout must be positive"):
            config.connection_timeout = -1
            config.validate()

        with pytest.raises(ValueError, match="cache_max_size_mb must be positive"):
            config.cache_max_size_mb = 0
            config.validate()

    def test_global_config(self):
        """Test global configuration management."""
        # Reset to default
        reset_performance_config()

        # Get default config
        config1 = get_performance_config()
        assert isinstance(config1, PerformanceConfig)

        # Set custom config
        custom_config = PerformanceConfig(max_connections=500)
        set_performance_config(custom_config)

        # Get updated config
        config2 = get_performance_config()
        assert config2.max_connections == 500

        # Reset again
        reset_performance_config()
        config3 = get_performance_config()
        assert config3.max_connections == 100  # Back to default
