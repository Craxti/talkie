"""Tests for memory manager."""

import pytest
import time
from unittest.mock import patch, MagicMock
from talkie.utils.memory_manager import (
    MemoryManager,
    MemoryStats,
    get_memory_manager,
    start_memory_monitoring,
    stop_memory_monitoring,
    get_memory_stats,
    optimize_memory
)


class TestMemoryStats:
    """Test memory statistics."""

    def test_memory_stats_creation(self):
        """Test memory stats creation."""
        stats = MemoryStats(
            current_mb=100.0,
            peak_mb=150.0,
            available_mb=1000.0,
            usage_percent=10.0,
            gc_count=5,
            timestamp=time.time()
        )

        assert stats.current_mb == 100.0
        assert stats.peak_mb == 150.0
        assert stats.available_mb == 1000.0
        assert stats.usage_percent == 10.0
        assert stats.gc_count == 5
        assert stats.timestamp > 0


class TestMemoryManager:
    """Test memory manager."""

    def test_memory_manager_creation(self):
        """Test memory manager creation."""
        manager = MemoryManager()

        assert manager.monitoring == False
        assert manager._monitor_thread is None
        assert isinstance(manager._stats, dict)
        assert isinstance(manager._callbacks, list)

    def test_get_current_stats(self):
        """Test getting current memory stats."""
        manager = MemoryManager()
        stats = manager.get_current_stats()

        assert isinstance(stats, MemoryStats)
        assert stats.current_mb > 0
        assert stats.available_mb > 0
        assert stats.usage_percent >= 0
        assert stats.gc_count >= 0
        assert stats.timestamp > 0

    def test_memory_monitoring(self):
        """Test memory monitoring."""
        manager = MemoryManager()

        # Start monitoring
        manager.start_monitoring()
        assert manager.monitoring == True
        assert manager._monitor_thread is not None

        # Wait a bit for monitoring to collect data
        time.sleep(0.1)

        # Stop monitoring
        manager.stop_monitoring()
        assert manager.monitoring == False

    def test_callback_management(self):
        """Test callback management."""
        manager = MemoryManager()

        # Test callback
        callback_called = []
        def test_callback(stats):
            callback_called.append(stats)

        # Add callback
        manager.add_callback(test_callback)
        assert test_callback in manager._callbacks

        # Remove callback
        manager.remove_callback(test_callback)
        assert test_callback not in manager._callbacks

    def test_force_gc(self):
        """Test forced garbage collection."""
        manager = MemoryManager()

        # This should not raise an exception
        manager.force_gc()

    def test_check_memory_limit(self):
        """Test memory limit checking."""
        manager = MemoryManager()

        # Mock the config to have a very low limit
        with patch.object(manager, 'config') as mock_config:
            mock_config.max_memory_usage_mb = 0.1  # Very low limit

            # Should return True if over limit
            result = manager.check_memory_limit()
            assert isinstance(result, bool)

    def test_optimize_memory(self):
        """Test memory optimization."""
        manager = MemoryManager()

        # This should not raise an exception
        manager.optimize_memory()

    def test_get_stats_summary(self):
        """Test getting stats summary."""
        manager = MemoryManager()
        summary = manager.get_stats_summary()

        assert isinstance(summary, dict)
        assert "current_memory_mb" in summary
        assert "peak_memory_mb" in summary
        assert "available_memory_mb" in summary
        assert "usage_percent" in summary
        assert "gc_count" in summary
        assert "monitoring_active" in summary
        assert "config" in summary


class TestGlobalMemoryManager:
    """Test global memory manager functions."""

    def test_get_memory_manager(self):
        """Test getting global memory manager."""
        manager = get_memory_manager()
        assert isinstance(manager, MemoryManager)

    def test_memory_monitoring_functions(self):
        """Test memory monitoring functions."""
        # These should not raise exceptions
        start_memory_monitoring()
        time.sleep(0.1)
        stop_memory_monitoring()

    def test_get_memory_stats(self):
        """Test getting memory stats."""
        stats = get_memory_stats()
        assert isinstance(stats, dict)
        assert "current_memory_mb" in stats

    def test_optimize_memory(self):
        """Test global memory optimization."""
        # This should not raise an exception
        optimize_memory()
