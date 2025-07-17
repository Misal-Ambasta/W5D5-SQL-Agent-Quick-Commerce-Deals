"""
Cache management with optional Redis support
"""
import os
import json
import hashlib
import logging
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)


class CacheNamespace(Enum):
    """Cache namespace enumeration for organizing cached data"""
    QUERY_RESULTS = "query_results"
    TABLE_EMBEDDINGS = "table_embeddings"
    SCHEMA_INFO = "schema_info"
    USER_SESSIONS = "user_sessions"
    API_RESPONSES = "api_responses"


class CacheBackend(ABC):
    """Abstract cache backend interface"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: str, ttl: int = 300) -> bool:
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend for development"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = 1000  # Maximum number of cached items
    
    async def get(self, key: str) -> Optional[str]:
        if key in self._cache:
            item = self._cache[key]
            # Check if expired
            if datetime.now() > item['expires_at']:
                del self._cache[key]
                return None
            return item['value']
        return None
    
    async def set(self, key: str, value: str, ttl: int = 300) -> bool:
        try:
            # Clean up expired items if cache is getting full
            if len(self._cache) >= self._max_size:
                await self._cleanup_expired()
            
            # If still full, remove oldest items
            if len(self._cache) >= self._max_size:
                # Remove 10% of oldest items
                items_to_remove = sorted(
                    self._cache.items(), 
                    key=lambda x: x[1]['created_at']
                )[:int(self._max_size * 0.1)]
                
                for item_key, _ in items_to_remove:
                    del self._cache[item_key]
            
            self._cache[key] = {
                'value': value,
                'created_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(seconds=ttl)
            }
            return True
        except Exception as e:
            logger.error(f"Memory cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        if key in self._cache:
            item = self._cache[key]
            if datetime.now() > item['expires_at']:
                del self._cache[key]
                return False
            return True
        return False
    
    async def _cleanup_expired(self):
        """Remove expired items from cache"""
        now = datetime.now()
        expired_keys = [
            key for key, item in self._cache.items()
            if now > item['expires_at']
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = datetime.now()
        active_items = sum(
            1 for item in self._cache.values()
            if now <= item['expires_at']
        )
        
        return {
            'total_items': len(self._cache),
            'active_items': active_items,
            'expired_items': len(self._cache) - active_items,
            'max_size': self._max_size
        }


class RedisCacheBackend(CacheBackend):
    """Redis cache backend for production"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[str]:
        try:
            value = await self.redis.get(key)
            return value.decode('utf-8') if value else None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: str, ttl: int = 300) -> bool:
        try:
            await self.redis.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        try:
            result = await self.redis.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False


class CacheManager:
    """Main cache manager with automatic backend selection"""
    
    def __init__(self):
        self.backend: Optional[CacheBackend] = None
        self.enabled = True
        self._initialize_backend()
    
    def _initialize_backend(self):
        """Initialize appropriate cache backend"""
        # Check if Redis should be skipped
        if os.getenv('SKIP_REDIS', '').lower() == 'true':
            logger.info("Redis disabled, using memory cache backend")
            self.backend = MemoryCacheBackend()
            return
        
        # Try to initialize Redis
        try:
            import redis.asyncio as redis
            from app.core.config import settings
            
            redis_client = redis.from_url(settings.redis_url)
            self.backend = RedisCacheBackend(redis_client)
            logger.info("Redis cache backend initialized")
            
        except ImportError:
            logger.warning("Redis not available, using memory cache backend")
            self.backend = MemoryCacheBackend()
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}, using memory cache backend")
            self.backend = MemoryCacheBackend()
    
    def _generate_cache_key(self, prefix: str, data: Union[str, Dict[str, Any]]) -> str:
        """Generate cache key from data"""
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        key_hash = hashlib.md5(data_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    async def get_query_result(self, query: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Get cached query result"""
        if not self.enabled or not self.backend:
            return None
        
        cache_data = {"query": query.lower().strip()}
        if context:
            cache_data["context"] = context
        
        cache_key = self._generate_cache_key("query", cache_data)
        
        try:
            cached_value = await self.backend.get(cache_key)
            if cached_value:
                return json.loads(cached_value)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None
    
    async def set_query_result(self, query: str, result: Dict[str, Any], 
                             context: Optional[Dict[str, Any]] = None, ttl: int = 300) -> bool:
        """Cache query result"""
        if not self.enabled or not self.backend:
            return False
        
        cache_data = {"query": query.lower().strip()}
        if context:
            cache_data["context"] = context
        
        cache_key = self._generate_cache_key("query", cache_data)
        
        try:
            # Add cache metadata
            cache_result = {
                **result,
                "cached": True,
                "cache_timestamp": datetime.now().isoformat()
            }
            
            cached_value = json.dumps(cache_result, default=str)
            return await self.backend.set(cache_key, cached_value, ttl)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def get_schema_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get cached schema information"""
        if not self.enabled or not self.backend:
            return None
        
        cache_key = self._generate_cache_key("schema", table_name)
        
        try:
            cached_value = await self.backend.get(cache_key)
            if cached_value:
                return json.loads(cached_value)
        except Exception as e:
            logger.error(f"Schema cache get error: {e}")
        
        return None
    
    async def set_schema_info(self, table_name: str, schema_info: Dict[str, Any], ttl: int = 3600) -> bool:
        """Cache schema information"""
        if not self.enabled or not self.backend:
            return False
        
        cache_key = self._generate_cache_key("schema", table_name)
        
        try:
            cached_value = json.dumps(schema_info, default=str)
            return await self.backend.set(cache_key, cached_value, ttl)
        except Exception as e:
            logger.error(f"Schema cache set error: {e}")
            return False
    
    async def clear_cache(self, pattern: Optional[str] = None) -> bool:
        """Clear cache (simplified implementation)"""
        if not self.enabled or not self.backend:
            return False
        
        # For memory cache, we can clear everything
        if isinstance(self.backend, MemoryCacheBackend):
            self.backend._cache.clear()
            return True
        
        # For Redis, this would require more complex pattern matching
        logger.warning("Cache clearing not fully implemented for Redis backend")
        return False
    
    async def get(self, key: str, namespace: Optional[str] = None, **kwargs) -> Optional[Dict[str, Any]]:
        """Get cached value with namespace support"""
        if not self.enabled or not self.backend:
            return None
        
        # Add namespace to key if provided
        cache_key = f"{namespace}:{key}" if namespace else key
        
        try:
            cached_value = await self.backend.get(cache_key)
            if cached_value:
                return json.loads(cached_value)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300, namespace: Optional[str] = None, **kwargs) -> bool:
        """Set cached value with namespace support"""
        if not self.enabled or not self.backend:
            return False
        
        # Add namespace to key if provided
        cache_key = f"{namespace}:{key}" if namespace else key
        
        try:
            cached_value = json.dumps(value, default=str)
            return await self.backend.set(cache_key, cached_value, ttl)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled or not self.backend:
            return {"enabled": False}
        
        stats = {
            "enabled": True,
            "backend_type": type(self.backend).__name__
        }
        
        if isinstance(self.backend, MemoryCacheBackend):
            stats.update(self.backend.get_stats())
        
        return stats


# Global cache manager instance
cache_manager = CacheManager()


# Convenience functions
async def get_cached_query_result(query: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Get cached query result"""
    return await cache_manager.get_query_result(query, context)


async def cache_query_result(query: str, result: Dict[str, Any], 
                           context: Optional[Dict[str, Any]] = None, ttl: int = 300) -> bool:
    """Cache query result"""
    return await cache_manager.set_query_result(query, result, context, ttl)


async def get_cached_schema_info(table_name: str) -> Optional[Dict[str, Any]]:
    """Get cached schema information"""
    return await cache_manager.get_schema_info(table_name)


async def cache_schema_info(table_name: str, schema_info: Dict[str, Any], ttl: int = 3600) -> bool:
    """Cache schema information"""
    return await cache_manager.set_schema_info(table_name, schema_info, ttl)