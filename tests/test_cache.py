"""Tests for cache module."""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest
import httpx
from talkie.utils.cache import (
    ResponseCache,
    CacheConfig,
    CacheEntry,
    CacheKeyData,
    get_cache,
    set_cache_config,
)


class TestCacheConfig:
    """Test cache configuration."""
    
    def test_default_config(self):
        """Test default cache configuration."""
        config = CacheConfig()
        assert config.enabled is True
        assert config.cache_dir == "~/.talkie/cache"
        assert config.default_ttl == 300
        assert config.max_entries == 1000
        assert config.max_size_mb == 100
        assert config.cache_get is True
        assert config.cache_post is False
        assert config.cache_put is False
        assert config.cache_delete is False
        assert config.cache_graphql is True

    def test_custom_config(self):
        """Test custom cache configuration."""
        config = CacheConfig(
            enabled=False,
            cache_dir="/tmp/test",
            default_ttl=600,
            max_entries=500,
            max_size_mb=50,
            cache_get=False,
            cache_post=True
        )
        assert config.enabled is False
        assert config.cache_dir == "/tmp/test"
        assert config.default_ttl == 600
        assert config.max_entries == 500
        assert config.max_size_mb == 50
        assert config.cache_get is False
        assert config.cache_post is True


class TestCacheEntry:
    """Test cache entry."""
    
    def test_cache_entry_creation(self):
        """Test cache entry creation."""
        entry = CacheEntry(
            url="https://example.com",
            method="GET",
            headers={"Content-Type": "application/json"},
            params={"page": 1},
            body=None,
            status_code=200,
            response_headers={"Content-Type": "application/json"},
            response_body='{"result": "success"}',
            cached_at=1234567890.0,
            expires_at=1234567890.0 + 300
        )
        assert entry.url == "https://example.com"
        assert entry.method == "GET"
        assert entry.status_code == 200
        assert entry.response_body == '{"result": "success"}'

    def test_cache_entry_expiration(self):
        """Test cache entry expiration."""
        now = time.time()
        entry = CacheEntry(
            url="https://example.com",
            method="GET",
            headers={},
            params=None,
            body=None,
            status_code=200,
            response_headers={},
            response_body="test",
            cached_at=now,
            expires_at=now + 1  # Expires in 1 second
        )
        
        # Should not be expired immediately
        assert not entry.is_expired()
        
        # Wait and check expiration
        time.sleep(1.1)
        assert entry.is_expired()

    def test_cache_entry_serialization(self):
        """Test cache entry serialization."""
        entry = CacheEntry(
            url="https://example.com",
            method="GET",
            headers={"Content-Type": "application/json"},
            params={"page": 1},
            body=None,
            status_code=200,
            response_headers={"Content-Type": "application/json"},
            response_body='{"result": "success"}',
            cached_at=1234567890.0,
            expires_at=1234567890.0 + 300
        )
        
        # Test to_dict
        data = entry.to_dict()
        assert data["url"] == "https://example.com"
        assert data["method"] == "GET"
        assert data["status_code"] == 200
        
        # Test from_dict
        new_entry = CacheEntry.from_dict(data)
        assert new_entry.url == entry.url
        assert new_entry.method == entry.method
        assert new_entry.status_code == entry.status_code


class TestResponseCache:
    """Test response cache."""
    
    def test_cache_initialization(self):
        """Test cache initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = CacheConfig(cache_dir=temp_dir)
            cache = ResponseCache(config)
            assert cache.config == config
            assert cache.cache_dir == Path(temp_dir)
            assert cache.index == {}

    def test_cache_key_generation(self):
        """Test cache key generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = CacheConfig(cache_dir=temp_dir)
            cache = ResponseCache(config)
            
            # Test basic key generation
            key_data1 = CacheKeyData(method="GET", url="https://example.com")
            key1 = cache._generate_cache_key(key_data1)
            key2 = cache._generate_cache_key(key_data1)
            assert key1 == key2  # Same request should generate same key
            
            # Test different requests generate different keys
            key_data3 = CacheKeyData(method="POST", url="https://example.com")
            key3 = cache._generate_cache_key(key_data3)
            assert key1 != key3
            
            # Test with headers
            key_data4 = CacheKeyData(
                method="GET",
                url="https://example.com",
                headers={"Authorization": "Bearer token"}
            )
            key_data5 = CacheKeyData(
                method="GET",
                url="https://example.com",
                headers={"Authorization": "Bearer different-token"}
            )
            key4 = cache._generate_cache_key(key_data4)
            key5 = cache._generate_cache_key(key_data5)
            assert key4 != key5

    def test_should_cache_request(self):
        """Test request caching logic."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = CacheConfig(cache_dir=temp_dir)
            cache = ResponseCache(config)
            
            # GET requests should be cached by default
            assert cache._should_cache_request("GET", {})
            
            # POST requests should not be cached by default
            assert not cache._should_cache_request("POST", {})
            
            # GraphQL queries should be cached
            headers = {"Content-Type": "application/json"}
            body = '{"query": "{ users { id name } }"}'
            assert cache._should_cache_request("POST", headers, body)
            
            # GraphQL mutations should not be cached
            body_mutation = '{"query": "mutation { createUser(name: \"test\") { id } }"}'
            assert not cache._should_cache_request("POST", headers, body_mutation)

    def test_cache_response_and_retrieval(self):
        """Test caching and retrieving responses."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = CacheConfig(cache_dir=temp_dir, default_ttl=3600)
            cache = ResponseCache(config)
            
            # Create mock response
            request = httpx.Request("GET", "https://example.com")
            response = httpx.Response(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content=b'{"result": "success"}',
                request=request
            )
            
            # Cache response
            cache.cache_response(response)
            
            # Retrieve cached response
            cached_response = cache.get_cached_response("GET", "https://example.com")
            assert cached_response is not None
            assert cached_response.status_code == 200
            assert cached_response.text == '{"result": "success"}'

    def test_cache_expiration(self):
        """Test cache expiration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = CacheConfig(cache_dir=temp_dir, default_ttl=1)  # 1 second TTL
            cache = ResponseCache(config)
            
            # Create and cache response
            request = httpx.Request("GET", "https://example.com")
            response = httpx.Response(
                status_code=200,
                content=b"test",
                request=request
            )
            cache.cache_response(response)
            
            # Should be available immediately
            cached_response = cache.get_cached_response("GET", "https://example.com")
            assert cached_response is not None
            
            # Wait for expiration
            time.sleep(1.1)
            
            # Should be expired now
            cached_response = cache.get_cached_response("GET", "https://example.com")
            assert cached_response is None

    def test_cache_cleanup(self):
        """Test cache cleanup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = CacheConfig(cache_dir=temp_dir, max_entries=2)
            cache = ResponseCache(config)
            
            # Add more entries than max_entries
            for i in range(3):
                request = httpx.Request("GET", f"https://example{i}.com")
                response = httpx.Response(
                    status_code=200,
                    content=f"response{i}".encode(),
                    request=request
                )
                cache.cache_response(response)
            
            # Should have only max_entries entries
            assert len(cache.index) <= config.max_entries

    def test_clear_cache(self):
        """Test clearing cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = CacheConfig(cache_dir=temp_dir)
            cache = ResponseCache(config)
            
            # Add some entries
            request = httpx.Request("GET", "https://example.com")
            response = httpx.Response(
                status_code=200,
                content=b"test",
                request=request
            )
            cache.cache_response(response)
            assert len(cache.index) > 0
            
            # Clear cache
            cache.clear_cache()
            assert len(cache.index) == 0

    def test_cache_stats(self):
        """Test cache statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = CacheConfig(cache_dir=temp_dir)
            cache = ResponseCache(config)
            
            stats = cache.get_cache_stats()
            assert "enabled" in stats
            assert "total_entries" in stats
            assert "total_size_mb" in stats
            assert "cache_dir" in stats
            assert "config" in stats
            assert stats["enabled"] is True
            assert stats["total_entries"] == 0


class TestGlobalCache:
    """Test global cache functions."""
    
    def test_get_cache(self):
        """Test getting global cache."""
        cache = get_cache()
        assert isinstance(cache, ResponseCache)

    def test_set_cache_config(self):
        """Test setting cache configuration."""
        config = CacheConfig(enabled=False)
        set_cache_config(config)
        cache = get_cache()
        assert cache.config.enabled is False