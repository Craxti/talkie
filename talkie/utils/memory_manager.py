"""Memory management utilities for Talkie."""

import gc
import threading
import time
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from ..utils.performance_config import get_performance_config

try:
    import psutil
except ImportError:
    psutil = None


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    current_mb: float
    peak_mb: float
    available_mb: float
    usage_percent: float
    gc_count: int
    timestamp: float


class MemoryManager:
    """Memory management and monitoring."""

    def __init__(self):
        self.config = get_performance_config()
        self.monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stats: Dict[str, MemoryStats] = {}
        self._callbacks: list[Callable[[MemoryStats], None]] = []
        self._lock = threading.Lock()

    def start_monitoring(self) -> None:
        """Start memory monitoring."""
        if self.monitoring:
            return

        self.monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop memory monitoring."""
        self.monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)

    def add_callback(self, callback: Callable[[MemoryStats], None]) -> None:
        """Add memory monitoring callback."""
        with self._lock:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[MemoryStats], None]) -> None:
        """Remove memory monitoring callback."""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    def get_current_stats(self) -> MemoryStats:
        """Get current memory statistics."""
        if psutil is None:
            return MemoryStats(
                current_mb=0.0,
                peak_mb=0.0,
                available_mb=0.0,
                usage_percent=0.0,
                gc_count=0,
                timestamp=time.time()
            )

        process = psutil.Process()
        memory_info = process.memory_info()

        # Get system memory info
        system_memory = psutil.virtual_memory()

        current_mb = memory_info.rss / 1024 / 1024
        available_mb = system_memory.available / 1024 / 1024
        usage_percent = system_memory.percent

        # Get GC stats
        gc_stats = gc.get_stats()
        gc_count = sum(stat['collections'] for stat in gc_stats)

        return MemoryStats(
            current_mb=current_mb,
            peak_mb=current_mb,  # Will be updated by monitoring
            available_mb=available_mb,
            usage_percent=usage_percent,
            gc_count=gc_count,
            timestamp=time.time()
        )

    def get_peak_memory(self) -> float:
        """Get peak memory usage in MB."""
        with self._lock:
            if not self._stats:
                return 0.0
            return max(stats.peak_mb for stats in self._stats.values())

    def force_gc(self) -> None:
        """Force garbage collection."""
        collected = gc.collect()
        if self.config.log_performance_metrics:
            print(f"Garbage collection freed {collected} objects")

    def check_memory_limit(self) -> bool:
        """Check if memory usage exceeds configured limit."""
        stats = self.get_current_stats()
        return stats.current_mb > self.config.max_memory_usage_mb

    def optimize_memory(self) -> None:
        """Optimize memory usage."""
        # Force garbage collection
        self.force_gc()

        # Check if we're over the limit
        if self.check_memory_limit():
            # Try to free more memory
            for _ in range(3):  # Try multiple times
                self.force_gc()
                if not self.check_memory_limit():
                    break

    def _monitor_loop(self) -> None:
        """Internal monitoring loop."""
        while self.monitoring:
            try:
                stats = self.get_current_stats()

                # Update peak memory
                with self._lock:
                    key = f"monitor_{threading.current_thread().ident}"
                    if key in self._stats:
                        stats.peak_mb = max(stats.current_mb, self._stats[key].peak_mb)
                    self._stats[key] = stats

                # Check memory limit
                if stats.current_mb > self.config.max_memory_usage_mb:
                    self.optimize_memory()

                # Call callbacks
                with self._lock:
                    for callback in self._callbacks:
                        try:
                            callback(stats)
                        except Exception:
                            pass  # Ignore callback errors

                # Sleep for a short time
                time.sleep(1.0)  # Monitor every second

            except Exception:
                break  # Exit gracefully on any error

    def get_stats_summary(self) -> Dict[str, Any]:
        """Get memory statistics summary."""
        with self._lock:
            if not self._stats:
                return {"error": "No monitoring data available"}

            current_stats = self.get_current_stats()
            peak_memory = self.get_peak_memory()

            return {
                "current_memory_mb": current_stats.current_mb,
                "peak_memory_mb": peak_memory,
                "available_memory_mb": current_stats.available_mb,
                "usage_percent": current_stats.usage_percent,
                "gc_count": current_stats.gc_count,
                "monitoring_active": self.monitoring,
                "config": {
                    "max_memory_mb": self.config.max_memory_usage_mb,
                    "gc_threshold": self.config.gc_threshold,
                    "memory_monitoring_enabled": self.config.enable_memory_monitoring
                }
            }


# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get global memory manager."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


def start_memory_monitoring() -> None:
    """Start global memory monitoring."""
    manager = get_memory_manager()
    manager.start_monitoring()


def stop_memory_monitoring() -> None:
    """Stop global memory monitoring."""
    manager = get_memory_manager()
    manager.stop_monitoring()


def get_memory_stats() -> Dict[str, Any]:
    """Get current memory statistics."""
    manager = get_memory_manager()
    return manager.get_stats_summary()


def optimize_memory() -> None:
    """Optimize memory usage."""
    manager = get_memory_manager()
    manager.optimize_memory()
