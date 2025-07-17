"""
Cache integration utilities for seamless caching across the application
"""
import functools
import hashlib
import logging
from typing import Any, Callable, Optional, List
from datetime import datetime

from app.core.cache import cache_manager, CacheNamespace

logger = logging.getLogger(__name__)


def cache_result(
    namespace: str = None,
    ttl: int = None,
    key_prefix: str = "",
    use_args: bool = True,
    use_kwargs: bool = True,
    tags: List[str] = None
):
    """
    Decorator for caching function results
    
    Args:
        namespace: Cache namespace
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        use_args: Include function args in cache key
        use_kwargs: Include function kwargs in cache key
        tags: Tags for cache invalidation
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _generate_function_cache_key(
                func, args, kwargs, key_prefix, use_args, use_kwargs
            )
            
            # Try to get from cache
            try:
                cached_result = await cache_manager.get(cache_key, namespace=namespace)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache get error for {func.__name__}: {e}")
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache the result
            try:
                await cache_manager.set(
                    cache_key, 
                    result, 
                    ttl=ttl, 
                    namespace=namespace,
                    tags=tags
                )
                logger.debug(f"Cached result for {func.__name__}: {cache_key}")
            except Exception as e:
                logger.warning(f"Cache set error for {func.__name__}: {e}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, we can't use async cache operations
            # This is a simplified version that could be enhanced
            return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def _generate_function_cache_key(
    func: Callable, 
    args: tuple, 
    kwargs: dict, 
    key_prefix: str,
    use_args: bool,
    use_kwargs: bool
) -> str:
    """Generate a cache key for a function call"""
    key_parts = [key_prefix, func.__name__]
    
    if use_args and args:
        # Convert args to string representation
        args_str = "_".join(str(arg) for arg in args)
        key_parts.append(f"args_{hashlib.md5(args_str.encode()).hexdigest()[:8]}")
    
    if use_kwargs and kwargs:
        # Sort kwargs for consistent key generation
        sorted_kwargs = sorted(kwargs.items())
        kwargs_str = "_".join(f"{k}={v}" for k, v in sorted_kwargs)
        key_parts.append(f"kwargs_{hashlib.md5(kwargs_str.encode()).hexdigest()[:8]}")
    
    return ":".join(key_parts)


class QueryResultCache:
    """Specialized cache for query results with intelligent invalidation"""
    
    @staticmethod
    async def get_cached_query(query_hash: str) -> Optional[dict]:
        """Get cached query result"""
        return await cache_manager.get_query_result(query_hash)
    
    @staticmethod
    async def cache_query(
        query_hash: str, 
        result: dict, 
        tables_used: List[str] = None,
        execution_time: float = None
    ) -> bool:
        """Cache query result with metadata"""
        # Add execution metadata
        cached_result = {
            "result": result,
            "cached_at": datetime.now().isoformat(),
            "execution_time": execution_time,
            "tables_used": tables_used or []
        }
        
        return await cache_manager.cache_query_result(
            query_hash, 
            cached_result, 
            tables_used=tables_used
        )
    
    @staticmethod
    async def invalidate_queries_for_tables(table_names: List[str]) -> int:
        """Invalidate all cached queries that use specific tables"""
        total_invalidated = 0
        for table_name in table_names:
            invalidated = await cache_manager.invalidate_table_cache(table_name)
            total_invalidated += invalidated
        return total_invalidated


class SchemaCache:
    """Specialized cache for database schema metadata"""
    
    @staticmethod
    async def get_table_schema(table_name: str) -> Optional[dict]:
        """Get cached table schema"""
        return await cache_manager.get_schema_metadata(table_name)
    
    @staticmethod
    async def cache_table_schema(table_name: str, schema: dict) -> bool:
        """Cache table schema metadata"""
        return await cache_manager.cache_schema_metadata(table_name, schema)
    
    @staticmethod
    async def invalidate_schema_cache() -> int:
        """Invalidate all schema cache entries"""
        return await cache_manager.invalidate_schema_cache()


class EmbeddingCache:
    """Specialized cache for table embeddings"""
    
    @staticmethod
    async def get_table_embeddings(table_name: str) -> Optional[Any]:
        """Get cached table embeddings"""
        return await cache_manager.get_table_embeddings(table_name)
    
    @staticmethod
    async def cache_table_embeddings(table_name: str, embeddings: Any) -> bool:
        """Cache table embeddings"""
        return await cache_manager.cache_table_embeddings(table_name, embeddings)
    
    @staticmethod
    async def invalidate_embeddings() -> int:
        """Invalidate all embedding cache entries"""
        return await cache_manager.invalidate_by_tags(["embeddings"])


# Import asyncio for function type checking
import asyncio