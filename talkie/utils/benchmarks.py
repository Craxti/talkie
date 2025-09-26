"""Performance benchmarking utilities for Talkie."""

import time
import asyncio
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, asdict
from pathlib import Path
import json

try:
    import psutil
except ImportError:
    psutil = None

from ..core.client import HttpClient
from ..core.async_client import AsyncHttpClient
from ..utils.cache import get_cache, CacheConfig, set_cache_config


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    name: str
    duration: float
    memory_usage_mb: float
    requests_per_second: float
    success_rate: float
    errors: List[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class BenchmarkSuite:
    """Collection of benchmark results."""
    name: str
    timestamp: float
    results: List[BenchmarkResult]
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "timestamp": self.timestamp,
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary
        }


class PerformanceMonitor:
    """Monitor system performance during benchmarks."""

    def __init__(self):
        self.monitoring = False
        self.data = []
        self._thread = None

    def start(self):
        """Start monitoring system performance."""
        self.monitoring = True
        self.data = []
        self._thread = threading.Thread(target=self._monitor_loop)
        self._thread.start()

    def stop(self) -> Dict[str, Any]:
        """Stop monitoring and return collected data."""
        self.monitoring = False
        if self._thread:
            self._thread.join()

        if not self.data:
            return {"cpu_usage": 0, "memory_usage_mb": 0}

        cpu_values = [d["cpu"] for d in self.data]
        memory_values = [d["memory"] for d in self.data]

        return {
            "cpu_usage": {
                "avg": statistics.mean(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values)
            },
            "memory_usage_mb": {
                "avg": statistics.mean(memory_values),
                "max": max(memory_values),
                "min": min(memory_values)
            }
        }

    def _monitor_loop(self):
        """Internal monitoring loop."""
        if psutil is None:
            return

        process = psutil.Process()
        while self.monitoring:
            try:
                cpu_percent = process.cpu_percent()
                memory_mb = process.memory_info().rss / 1024 / 1024

                # Limit data collection to prevent memory leaks
                if len(self.data) > 1000:  # Keep only last 1000 measurements
                    self.data = self.data[-500:]  # Keep last 500

                self.data.append({
                    "timestamp": time.time(),
                    "cpu": cpu_percent,
                    "memory": memory_mb
                })

                time.sleep(0.1)  # Monitor every 100ms
            except Exception:
                break  # Exit gracefully on any error


class BenchmarkRunner:
    """Runner for performance benchmarks."""

    def __init__(self, output_dir: str = "benchmarks"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.monitor = PerformanceMonitor()

    def run_http_benchmark(
        self,
        url: str,
        num_requests: int = 100,
        concurrent_requests: int = 10,
        use_cache: bool = False
    ) -> BenchmarkResult:
        """Run HTTP request benchmark."""
        name = f"HTTP-{num_requests}req-{concurrent_requests}concurrent"
        if use_cache:
            name += "-cached"

        errors = []
        successful_requests = 0

        # Configure cache if needed
        if use_cache:
            cache_config = CacheConfig(enabled=True, default_ttl=300)
            set_cache_config(cache_config)

        # Start performance monitoring
        self.monitor.start()
        start_time = time.time()

        def make_request(client: HttpClient) -> bool:
            """Make a single HTTP request."""
            try:
                response = client.request("GET", url)
                return response.status_code == 200
            except Exception as e:
                errors.append(str(e))
                return False

        # Create client instances for concurrent requests
        clients = [HttpClient(enable_cache=use_cache) for _ in range(concurrent_requests)]

        # Execute requests in batches
        batch_size = num_requests // concurrent_requests
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = []

            for batch in range(concurrent_requests):
                client = clients[batch]
                requests_in_batch = batch_size
                if batch == concurrent_requests - 1:
                    # Last batch gets any remaining requests
                    requests_in_batch += num_requests % concurrent_requests

                for _ in range(requests_in_batch):
                    future = executor.submit(make_request, client)
                    futures.append(future)

            # Collect results
            for future in as_completed(futures):
                if future.result():
                    successful_requests += 1

        # Calculate metrics
        end_time = time.time()
        duration = end_time - start_time
        performance_data = self.monitor.stop()

        requests_per_second = num_requests / duration if duration > 0 else 0
        success_rate = (successful_requests / num_requests) * 100
        memory_usage = performance_data.get("memory_usage_mb", {}).get("avg", 0)

        return BenchmarkResult(
            name=name,
            duration=duration,
            memory_usage_mb=memory_usage,
            requests_per_second=requests_per_second,
            success_rate=success_rate,
            errors=errors[:10],  # Limit errors in output
            metadata={
                "url": url,
                "num_requests": num_requests,
                "concurrent_requests": concurrent_requests,
                "use_cache": use_cache,
                "performance": performance_data
            }
        )

    async def run_async_benchmark(
        self,
        urls: List[str],
        concurrent_requests: int = 50
    ) -> BenchmarkResult:
        """Run async HTTP benchmark."""
        name = f"Async-{len(urls)}urls-{concurrent_requests}concurrent"

        errors = []
        successful_requests = 0

        # Start performance monitoring
        self.monitor.start()
        start_time = time.time()

        async def make_async_request(client: AsyncHttpClient, url: str) -> bool:
            """Make a single async HTTP request."""
            try:
                response = await client.request("GET", url)
                return True
            except Exception as e:
                errors.append(str(e))
                return False

        # Create async client
        client = AsyncHttpClient(max_concurrent=concurrent_requests)

        # Execute all requests concurrently
        semaphore = asyncio.Semaphore(concurrent_requests)

        async def bounded_request(url: str) -> bool:
            async with semaphore:
                return await make_async_request(client, url)

        tasks = [bounded_request(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful requests
        successful_requests = sum(1 for r in results if r is True)

        # Calculate metrics
        end_time = time.time()
        duration = end_time - start_time
        performance_data = self.monitor.stop()

        requests_per_second = len(urls) / duration if duration > 0 else 0
        success_rate = (successful_requests / len(urls)) * 100
        memory_usage = performance_data.get("memory_usage_mb", {}).get("avg", 0)

        return BenchmarkResult(
            name=name,
            duration=duration,
            memory_usage_mb=memory_usage,
            requests_per_second=requests_per_second,
            success_rate=success_rate,
            errors=errors[:10],
            metadata={
                "urls": urls[:5],  # Sample URLs
                "total_urls": len(urls),
                "concurrent_requests": concurrent_requests,
                "performance": performance_data
            }
        )

    def run_cache_benchmark(
        self,
        url: str,
        num_requests: int = 1000
    ) -> BenchmarkResult:
        """Benchmark cache performance."""
        name = f"Cache-{num_requests}req"

        # Configure cache
        cache_config = CacheConfig(enabled=True, default_ttl=300)
        set_cache_config(cache_config)

        # Clear cache first
        cache = get_cache()
        cache.clear_cache()

        errors = []
        cache_hits = 0
        cache_misses = 0

        # Start performance monitoring
        self.monitor.start()
        start_time = time.time()

        client = HttpClient(enable_cache=True)

        # First request to populate cache
        try:
            client.request("GET", url)
            cache_misses += 1
        except Exception as e:
            errors.append(str(e))

        # Subsequent requests should hit cache
        for _ in range(num_requests - 1):
            try:
                # Check if response comes from cache
                cache_response = cache.get_cached_response("GET", url)
                if cache_response:
                    cache_hits += 1
                else:
                    client.request("GET", url)
                    cache_misses += 1
            except Exception as e:
                errors.append(str(e))

        # Calculate metrics
        end_time = time.time()
        duration = end_time - start_time
        performance_data = self.monitor.stop()

        requests_per_second = num_requests / duration if duration > 0 else 0
        cache_hit_rate = (cache_hits / num_requests) * 100
        memory_usage = performance_data.get("memory_usage_mb", {}).get("avg", 0)

        return BenchmarkResult(
            name=name,
            duration=duration,
            memory_usage_mb=memory_usage,
            requests_per_second=requests_per_second,
            success_rate=100.0 - (len(errors) / num_requests * 100),
            errors=errors[:10],
            metadata={
                "url": url,
                "num_requests": num_requests,
                "cache_hits": cache_hits,
                "cache_misses": cache_misses,
                "cache_hit_rate": cache_hit_rate,
                "performance": performance_data
            }
        )

    def run_memory_stress_test(
        self,
        num_clients: int = 100,
        requests_per_client: int = 10,
        url: str = "http://httpbin.org/json"
    ) -> BenchmarkResult:
        """Run memory stress test with multiple clients."""
        name = f"MemoryStress-{num_clients}clients-{requests_per_client}req"

        errors = []
        successful_requests = 0

        # Start performance monitoring
        self.monitor.start()
        start_time = time.time()

        def client_worker(client_id: int) -> int:
            """Worker function for a single client."""
            client = HttpClient()
            local_success = 0

            for _ in range(requests_per_client):
                try:
                    response = client.request("GET", url)
                    if response.status_code == 200:
                        local_success += 1
                except Exception as e:
                    errors.append(f"Client {client_id}: {str(e)}")

            return local_success

        # Run multiple clients concurrently
        with ThreadPoolExecutor(max_workers=min(num_clients, 50)) as executor:
            futures = [
                executor.submit(client_worker, i)
                for i in range(num_clients)
            ]

            for future in as_completed(futures):
                successful_requests += future.result()

        # Calculate metrics
        end_time = time.time()
        duration = end_time - start_time
        performance_data = self.monitor.stop()

        total_requests = num_clients * requests_per_client
        requests_per_second = total_requests / duration if duration > 0 else 0
        success_rate = (successful_requests / total_requests) * 100
        memory_usage = performance_data.get("memory_usage_mb", {}).get("max", 0)

        return BenchmarkResult(
            name=name,
            duration=duration,
            memory_usage_mb=memory_usage,
            requests_per_second=requests_per_second,
            success_rate=success_rate,
            errors=errors[:10],
            metadata={
                "num_clients": num_clients,
                "requests_per_client": requests_per_client,
                "total_requests": total_requests,
                "performance": performance_data
            }
        )

    def run_full_benchmark_suite(
        self,
        test_url: str = "http://httpbin.org/json"
    ) -> BenchmarkSuite:
        """Run complete benchmark suite."""
        suite_name = f"Talkie-Benchmark-{int(time.time())}"
        start_time = time.time()

        results = []

        # HTTP benchmarks
        results.append(
            self.run_http_benchmark(test_url, 100, 10, use_cache=False)
        )
        results.append(
            self.run_http_benchmark(test_url, 100, 10, use_cache=True)
        )

        # Cache benchmark
        results.append(
            self.run_cache_benchmark(test_url, 500)
        )

        # Memory stress test
        results.append(
            self.run_memory_stress_test(50, 5, test_url)
        )

        # Async benchmark
        urls = [f"{test_url}?id={i}" for i in range(100)]
        async_result = asyncio.run(self.run_async_benchmark(urls, 20))
        results.append(async_result)

        # Calculate summary
        total_duration = time.time() - start_time
        avg_rps = statistics.mean([r.requests_per_second for r in results])
        avg_memory = statistics.mean([r.memory_usage_mb for r in results])
        avg_success_rate = statistics.mean([r.success_rate for r in results])

        summary = {
            "total_duration": total_duration,
            "average_requests_per_second": avg_rps,
            "average_memory_usage_mb": avg_memory,
            "average_success_rate": avg_success_rate,
            "total_benchmarks": len(results),
            "test_url": test_url
        }

        suite = BenchmarkSuite(
            name=suite_name,
            timestamp=start_time,
            results=results,
            summary=summary
        )

        # Save results
        self.save_benchmark_suite(suite)

        return suite

    def save_benchmark_suite(self, suite: BenchmarkSuite) -> str:
        """Save benchmark suite to file."""
        filename = f"{suite.name}.json"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(suite.to_dict(), f, indent=2, ensure_ascii=False)

        return str(filepath)

    def load_benchmark_suite(self, filepath: str) -> BenchmarkSuite:
        """Load benchmark suite from file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        results = [
            BenchmarkResult(**result_data)
            for result_data in data["results"]
        ]

        return BenchmarkSuite(
            name=data["name"],
            timestamp=data["timestamp"],
            results=results,
            summary=data["summary"]
        )

    def compare_benchmark_suites(
        self,
        suite1: BenchmarkSuite,
        suite2: BenchmarkSuite
    ) -> Dict[str, Any]:
        """Compare two benchmark suites."""
        comparison = {
            "suite1": {"name": suite1.name, "timestamp": suite1.timestamp},
            "suite2": {"name": suite2.name, "timestamp": suite2.timestamp},
            "comparisons": []
        }

        # Match benchmarks by name
        suite1_by_name = {r.name: r for r in suite1.results}
        suite2_by_name = {r.name: r for r in suite2.results}

        common_benchmarks = set(suite1_by_name.keys()) & set(suite2_by_name.keys())

        for benchmark_name in common_benchmarks:
            r1 = suite1_by_name[benchmark_name]
            r2 = suite2_by_name[benchmark_name]

            rps_change = ((r2.requests_per_second - r1.requests_per_second) / r1.requests_per_second * 100) if r1.requests_per_second > 0 else 0
            memory_change = ((r2.memory_usage_mb - r1.memory_usage_mb) / r1.memory_usage_mb * 100) if r1.memory_usage_mb > 0 else 0
            duration_change = ((r2.duration - r1.duration) / r1.duration * 100) if r1.duration > 0 else 0

            comparison["comparisons"].append({
                "benchmark": benchmark_name,
                "requests_per_second": {
                    "suite1": r1.requests_per_second,
                    "suite2": r2.requests_per_second,
                    "change_percent": rps_change
                },
                "memory_usage_mb": {
                    "suite1": r1.memory_usage_mb,
                    "suite2": r2.memory_usage_mb,
                    "change_percent": memory_change
                },
                "duration": {
                    "suite1": r1.duration,
                    "suite2": r2.duration,
                    "change_percent": duration_change
                },
                "success_rate": {
                    "suite1": r1.success_rate,
                    "suite2": r2.success_rate,
                    "change_percent": r2.success_rate - r1.success_rate
                }
            })

        return comparison
