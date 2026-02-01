"""Request/response caching utilities for Talkie."""

import os
import json
import hashlib
import time
from typing import Any, Dict, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

import httpx
from pydantic import BaseModel, Field


@dataclass
class CacheEntry:
    """Represents a cached response entry."""
    url: str
    method: str
    headers: Dict[str, str]
    params: Optional[Dict[str, Any]]
    body: Optional[str]
    status_code: int
    response_headers: Dict[str, str]
    response_body: str
    cached_at: float
    expires_at: float

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class CacheKeyData:
    """Data structure for cache key generation."""
    method: str
    url: str
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    body: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create instance from dictionary."""
        return cls(**data)


class CacheConfig(BaseModel):
    """Cache configuration."""
    enabled: bool = Field(True, description="Enable caching")
    cache_dir: str = Field("~/.talkie/cache", description="Cache directory path")
    default_ttl: int = Field(300, description="Default TTL in seconds (5 minutes)")
    max_entries: int = Field(1000, description="Maximum number of cache entries")
    max_size_mb: int = Field(100, description="Maximum cache size in MB")

    # Cache policies by method
    cache_get: bool = Field(True, description="Cache GET requests")
    cache_post: bool = Field(False, description="Cache POST requests")
    cache_put: bool = Field(False, description="Cache PUT requests")
    cache_delete: bool = Field(False, description="Cache DELETE requests")
    cache_graphql: bool = Field(True, description="Cache GraphQL queries (only queries, not mutations)")


class ResponseCache:
    """HTTP response cache manager."""

    def __init__(self, config: Optional[CacheConfig] = None):
        """
        Initialize cache manager.

        Args:
            config: Cache configuration
        """
        self.config = config or CacheConfig()
        self.cache_dir = Path(os.path.expanduser(self.config.cache_dir))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache index file
        self.index_file = self.cache_dir / "index.json"
        self.index = self._load_index()

    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """Load cache index from disk."""
        if not self.index_file.exists():
            return {}

        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_index(self) -> None:
        """Save cache index to disk."""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2, ensure_ascii=False)
        except IOError:
            pass  # Ignore write errors

    def _generate_cache_key(self, key_data: CacheKeyData) -> str:
        """
        Generate cache key for request.

        Args:
            key_data: Cache key data structure

        Returns:
            Cache key string
        """
        # Normalize inputs
        method = key_data.method.upper()
        url = key_data.url.lower()

        # Only include Authorization header in cache key
        auth_header = {}
        if key_data.headers and 'Authorization' in key_data.headers:
            auth_header['Authorization'] = key_data.headers['Authorization']

        # Create cache key components
        key_components = {
            'method': method,
            'url': url,
            'headers': auth_header,
            'params': key_data.params or {},
            'body': key_data.body or ''
        }

        # Generate hash
        key_string = json.dumps(key_components, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()

    def _should_cache_request(
        self,
        method: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None
    ) -> bool:
        """
        Check if request should be cached based on configuration.

        Args:
            method: HTTP method
            headers: Request headers
            body: Request body

        Returns:
            True if request should be cached
        """
        if not self.config.enabled:
            return False

        method = method.upper()

        # Method-specific caching rules
        cache_rules = {
            'GET': self.config.cache_get,
            'PUT': self.config.cache_put,
            'DELETE': self.config.cache_delete
        }

        # Handle POST requests with special GraphQL logic
        if method == 'POST':
            if (self.config.cache_graphql and
                headers and
                headers.get('Content-Type', '').startswith('application/json') and
                body and 'query' in body and 'mutation' not in body.lower()):
                return True
            return self.config.cache_post

        return cache_rules.get(method, False)

    def get_cached_response(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[str] = None
    ) -> Optional[httpx.Response]:
        """
        Get cached response if available and not expired.

        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            params: Query parameters
            body: Request body

        Returns:
            Cached response or None if not found/expired
        """
        if not self._should_cache_request(method, headers, body):
            return None

        key_data = CacheKeyData(method=method, url=url, headers=headers, params=params, body=body)
        cache_key = self._generate_cache_key(key_data)

        # Check if entry exists in index
        if cache_key not in self.index:
            return None

        entry_info = self.index[cache_key]
        cache_file = self.cache_dir / f"{cache_key}.json"

        # Check if cache file exists
        if not cache_file.exists():
            # Remove from index if file is missing
            del self.index[cache_key]
            self._save_index()
            return None

        try:
            # Load cache entry
            with open(cache_file, 'r', encoding='utf-8') as f:
                entry_data = json.load(f)

            entry = CacheEntry.from_dict(entry_data)

            # Check if expired
            if entry.is_expired():
                # Remove expired entry
                cache_file.unlink(missing_ok=True)
                del self.index[cache_key]
                self._save_index()
                return None

            # Create httpx.Response object
            response = httpx.Response(
                status_code=entry.status_code,
                headers=entry.response_headers,
                content=entry.response_body.encode('utf-8'),
                request=httpx.Request(method, url)
            )

            return response

        except (json.JSONDecodeError, IOError, KeyError):
            # Remove corrupted entry
            cache_file.unlink(missing_ok=True)
            if cache_key in self.index:
                del self.index[cache_key]
                self._save_index()
            return None

    def cache_response(
        self,
        response: httpx.Response,
        ttl: Optional[int] = None,
        max_size_mb: float = 1.0
    ) -> None:
        """
        Cache HTTP response.

        Args:
            response: HTTP response to cache
            ttl: Time to live in seconds (uses default if None)
            max_size_mb: Maximum response size to cache in MB
        """
        # Skip caching if response is too large
        response_size_mb = len(response.content) / (1024 * 1024)
        if response_size_mb > max_size_mb:
            return
        request = response.request
        method = request.method
        url = str(request.url)
        headers = dict(request.headers)

        # Extract params and body
        params = dict(request.url.params) if request.url.params else None
        body = None
        if hasattr(request, 'content') and request.content:
            body = request.content.decode('utf-8')
        elif hasattr(request, '_content') and request._content:
            body = request._content.decode('utf-8')

        if not self._should_cache_request(method, headers, body):
            return

        # Use provided TTL or default
        ttl = ttl or self.config.default_ttl

        # Create cache entry
        now = time.time()
        entry = CacheEntry(
            url=url,
            method=method,
            headers=headers,
            params=params,
            body=body,
            status_code=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.text,
            cached_at=now,
            expires_at=now + ttl
        )

        key_data = CacheKeyData(method=method, url=url, headers=headers, params=params, body=body)
        cache_key = self._generate_cache_key(key_data)
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            # Save cache entry
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(entry.to_dict(), f, indent=2, ensure_ascii=False)

            # Update index
            self.index[cache_key] = {
                'url': url,
                'method': method,
                'cached_at': now,
                'expires_at': entry.expires_at,
                'size': cache_file.stat().st_size
            }

            # Cleanup if needed
            self._cleanup_cache()
            self._save_index()

        except IOError:
            pass  # Ignore write errors

    def _cleanup_cache(self) -> None:
        """Clean up expired entries and enforce size limits."""
        now = time.time()

        # Remove expired entries
        expired_keys = []
        for cache_key, entry_info in self.index.items():
            if entry_info['expires_at'] < now:
                expired_keys.append(cache_key)

        for key in expired_keys:
            cache_file = self.cache_dir / f"{key}.json"
            cache_file.unlink(missing_ok=True)
            del self.index[key]

        # Enforce max entries limit
        if len(self.index) > self.config.max_entries:
            # Sort by access time, remove oldest
            sorted_entries = sorted(
                self.index.items(),
                key=lambda x: x[1]['cached_at']
            )

            entries_to_remove = len(self.index) - self.config.max_entries
            for key, _ in sorted_entries[:entries_to_remove]:
                cache_file = self.cache_dir / f"{key}.json"
                cache_file.unlink(missing_ok=True)
                del self.index[key]

        # Check total cache size
        total_size = sum(entry['size'] for entry in self.index.values())
        max_size_bytes = self.config.max_size_mb * 1024 * 1024

        if total_size > max_size_bytes:
            # Remove oldest entries until under size limit
            sorted_entries = sorted(
                self.index.items(),
                key=lambda x: x[1]['cached_at']
            )

            for key, entry_info in sorted_entries:
                cache_file = self.cache_dir / f"{key}.json"
                cache_file.unlink(missing_ok=True)
                total_size -= entry_info['size']
                del self.index[key]

                if total_size <= max_size_bytes:
                    break

    def clear_cache(self) -> None:
        """Clear all cached entries."""
        # Remove all cache files
        for cache_file in self.cache_dir.glob("*.json"):
            if cache_file.name != "index.json":
                cache_file.unlink(missing_ok=True)

        # Clear index
        self.index.clear()
        self._save_index()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_size = sum(entry['size'] for entry in self.index.values())

        return {
            'enabled': self.config.enabled,
            'total_entries': len(self.index),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'cache_dir': str(self.cache_dir),
            'config': self.config.model_dump()
        }


# Global cache instance
_global_cache: Optional[ResponseCache] = None


def get_cache() -> ResponseCache:
    """Get global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = ResponseCache()
    return _global_cache


def set_cache_config(config: CacheConfig) -> None:
    """Set global cache configuration."""
    global _global_cache
    _global_cache = ResponseCache(config)
