"""Tests for response caching functionality."""

import pytest
import tempfile
import shutil
import time
from pathlib import Path
from unittest.mock import Mock, patch

import httpx

from talkie.utils.cache import ResponseCache, CacheConfig, CacheEntry


class TestCacheEntry:
    """Test cases for CacheEntry class."""

    def test_cache_entry_creation(self):
        """Test cache entry creation."""
        entry = CacheEntry(
            url="https://api.example.com/users",
            method="GET",
            headers={"Accept": "application/json"},
            params={"page": "1"},
            body=None,
            status_code=200,
            response_headers={"Content-Type": "application/json"},
            response_body='{"users": []}',
            cached_at=time.time(),
            expires_at=time.time() + 300
        )

        assert entry.url == "https://api.example.com/users"
        assert entry.method == "GET"
        assert entry.status_code == 200
        assert not entry.is_expired()

    def test_cache_entry_expiration(self):
        """Test cache entry expiration check."""
        # Create expired entry
        entry = CacheEntry(
            url="https://api.example.com/users",
            method="GET",
            headers={},
            params=None,
            body=None,
            status_code=200,
            response_headers={},
            response_body="{}",
            cached_at=time.time() - 400,
            expires_at=time.time() - 100  # Expired 100 seconds ago
        )

        assert entry.is_expired()

    def test_cache_entry_serialization(self):
        """Test cache entry serialization/deserialization."""
        original = CacheEntry(
            url="https://api.example.com/users",
            method="GET",
            headers={"Accept": "application/json"},
            params={"page": "1"},
            body=None,
            status_code=200,
            response_headers={"Content-Type": "application/json"},
            response_body='{"users": []}',
            cached_at=time.time(),
            expires_at=time.time() + 300
        )

        # Convert to dict and back
        data = original.to_dict()
        restored = CacheEntry.from_dict(data)

        assert restored.url == original.url
        assert restored.method == original.method
        assert restored.status_code == original.status_code
        assert restored.response_body == original.response_body


class TestCacheConfig:
    """Test cases for CacheConfig class."""

    def test_default_config(self):
        """Test default cache configuration."""
        config = CacheConfig()

        assert config.enabled is True
        assert config.default_ttl == 300
        assert config.max_entries == 1000
        assert config.max_size_mb == 100
        assert config.cache_get is True
        assert config.cache_post is False
        assert config.cache_graphql is True

    def test_custom_config(self):
        """Test custom cache configuration."""
        config = CacheConfig(
            enabled=False,
            default_ttl=600,
            max_entries=500,
            cache_get=False,
            cache_graphql=False
        )

        assert config.enabled is False
        assert config.default_ttl == 600
        assert config.max_entries == 500
        assert config.cache_get is False
        assert config.cache_graphql is False


class TestResponseCache:
    """Test cases for ResponseCache class."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def cache(self, temp_cache_dir):
        """Create cache instance with temporary directory."""
        config = CacheConfig(cache_dir=temp_cache_dir)
        return ResponseCache(config)

    def test_cache_initialization(self, cache):
        """Test cache initialization."""
        assert cache.config.enabled is True
        assert cache.cache_dir.exists()
        assert cache.index == {}

    def test_generate_cache_key(self, cache):
        """Test cache key generation."""
        key1 = cache._generate_cache_key("GET", "https://api.example.com/users")
        key2 = cache._generate_cache_key("GET", "https://api.example.com/users")
        key3 = cache._generate_cache_key("POST", "https://api.example.com/users")

        # Same request should generate same key
        assert key1 == key2

        # Different methods should generate different keys
        assert key1 != key3

    def test_should_cache_request(self, cache):
        """Test request caching policy."""
        # GET requests should be cached
        assert cache._should_cache_request("GET")

        # POST requests should not be cached by default
        assert not cache._should_cache_request("POST")

        # GraphQL queries should be cached
        headers = {"Content-Type": "application/json"}
        body = '{"query": "query { users { id } }"}'
        assert cache._should_cache_request("POST", headers, body)

        # GraphQL mutations should not be cached
        body = '{"query": "mutation { createUser(name: \\"John\\") { id } }"}'
        assert not cache._should_cache_request("POST", headers, body)

    def test_cache_and_retrieve_response(self, cache):
        """Test caching and retrieving responses."""
        # Create mock response
        request = httpx.Request("GET", "https://api.example.com/users")
        response = httpx.Response(
            status_code=200,
            headers={"Content-Type": "application/json"},
            content=b'{"users": []}',
            request=request
        )

        # Cache response
        cache.cache_response(response)

        # Retrieve from cache
        cached = cache.get_cached_response("GET", "https://api.example.com/users")

        assert cached is not None
        assert cached.status_code == 200
        assert cached.text == '{"users": []}'

    def test_cache_expiration(self, cache):
        """Test cache expiration."""
        # Create mock response
        request = httpx.Request("GET", "https://api.example.com/users")
        response = httpx.Response(
            status_code=200,
            headers={"Content-Type": "application/json"},
            content=b'{"users": []}',
            request=request
        )

        # Cache with very short TTL
        cache.cache_response(response, ttl=1)

        # Should be available immediately
        cached = cache.get_cached_response("GET", "https://api.example.com/users")
        assert cached is not None

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired now
        cached = cache.get_cached_response("GET", "https://api.example.com/users")
        assert cached is None

    def test_cache_disabled(self, temp_cache_dir):
        """Test behavior when cache is disabled."""
        config = CacheConfig(cache_dir=temp_cache_dir, enabled=False)
        cache = ResponseCache(config)

        # Should not cache when disabled
        assert not cache._should_cache_request("GET")

        # Should return None for cache lookups
        cached = cache.get_cached_response("GET", "https://api.example.com/users")
        assert cached is None

    def test_clear_cache(self, cache):
        """Test cache clearing."""
        # Create and cache a response
        request = httpx.Request("GET", "https://api.example.com/users")
        response = httpx.Response(
            status_code=200,
            headers={"Content-Type": "application/json"},
            content=b'{"users": []}',
            request=request
        )

        cache.cache_response(response)

        # Verify it's cached
        assert len(cache.index) > 0

        # Clear cache
        cache.clear_cache()

        # Verify it's empty
        assert len(cache.index) == 0
        cached = cache.get_cached_response("GET", "https://api.example.com/users")
        assert cached is None

    def test_cache_stats(self, cache):
        """Test cache statistics."""
        stats = cache.get_cache_stats()

        assert 'enabled' in stats
        assert 'total_entries' in stats
        assert 'total_size_mb' in stats
        assert 'cache_dir' in stats
        assert 'config' in stats

        assert stats['enabled'] is True
        assert stats['total_entries'] == 0
        assert stats['total_size_mb'] == 0.0

    def test_max_entries_cleanup(self, temp_cache_dir):
        """Test cleanup when max entries limit is reached."""
        config = CacheConfig(cache_dir=temp_cache_dir, max_entries=2)
        cache = ResponseCache(config)

        # Create multiple responses to cache
        for i in range(3):
            request = httpx.Request("GET", f"https://api.example.com/users/{i}")
            response = httpx.Response(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content=f'{{"user": {i}}}'.encode(),
                request=request
            )
            cache.cache_response(response)
            time.sleep(0.1)  # Ensure different timestamps

        # Should only keep max_entries (2) entries
        assert len(cache.index) <= 2

    def test_cache_with_variables(self, cache):
        """Test caching with different URLs."""
        # Create and cache responses for different URLs
        request1 = httpx.Request("GET", "https://api.example.com/users/1")
        response1 = httpx.Response(
            status_code=200,
            headers={"Content-Type": "application/json"},
            content=b'{"user": {"id": 1}}',
            request=request1
        )

        request2 = httpx.Request("GET", "https://api.example.com/users/2")
        response2 = httpx.Response(
            status_code=200,
            headers={"Content-Type": "application/json"},
            content=b'{"user": {"id": 2}}',
            request=request2
        )

        cache.cache_response(response1)
        cache.cache_response(response2)

        # Should be able to retrieve both
        cached1 = cache.get_cached_response("GET", "https://api.example.com/users/1")
        cached2 = cache.get_cached_response("GET", "https://api.example.com/users/2")

        assert cached1 is not None
        assert cached2 is not None
        assert '"id": 1' in cached1.text
        assert '"id": 2' in cached2.text
