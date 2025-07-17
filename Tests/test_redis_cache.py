#!/usr/bin/env python3
"""
Test script for Redis caching system
"""
import asyncio
import json
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.cache import cache_manager, CacheNamespace


async def test_basic_cache_operations():
    """Test basic cache operations"""
    print("Testing basic cache operations...")
    
    # Test set and get
    test_key = "test_key"
    test_value = {"message": "Hello, Redis!", "timestamp": "2024-01-01T00:00:00"}
    
    # Set value
    success = await cache_manager.set(test_key, test_value, ttl=60)
    print(f"Set operation: {'SUCCESS' if success else 'FAILED'}")
    
    # Get value
    retrieved_value = await cache_manager.get(test_key)
    print(f"Get operation: {'SUCCESS' if retrieved_value == test_value else 'FAILED'}")
    print(f"Retrieved value: {retrieved_value}")
    
    # Test exists
    exists = await cache_manager.exists(test_key)
    print(f"Exists operation: {'SUCCESS' if exists else 'FAILED'}")
    
    # Test delete
    deleted = await cache_manager.delete(test_key)
    print(f"Delete operation: {'SUCCESS' if deleted else 'FAILED'}")
    
    # Verify deletion
    after_delete = await cache_manager.get(test_key)
    print(f"After delete check: {'SUCCESS' if after_delete is None else 'FAILED'}")


async def test_namespace_operations():
    """Test namespace-based cache operations"""
    print("\nTesting namespace operations...")
    
    namespace = CacheNamespace.QUERY_RESULTS.value
    
    # Set multiple values in namespace
    test_data = [
        ("query1", {"result": "data1", "count": 10}),
        ("query2", {"result": "data2", "count": 20}),
        ("query3", {"result": "data3", "count": 30})
    ]
    
    for key, value in test_data:
        success = await cache_manager.set(key, value, namespace=namespace, ttl=120)
        print(f"Set {key} in namespace: {'SUCCESS' if success else 'FAILED'}")
    
    # Retrieve values
    for key, expected_value in test_data:
        retrieved = await cache_manager.get(key, namespace=namespace)
        success = retrieved == expected_value
        print(f"Get {key} from namespace: {'SUCCESS' if success else 'FAILED'}")
    
    # Test namespace invalidation
    invalidated_count = await cache_manager.invalidate_namespace(namespace)
    print(f"Invalidated {invalidated_count} entries from namespace")
    
    # Verify invalidation
    for key, _ in test_data:
        retrieved = await cache_manager.get(key, namespace=namespace)
        success = retrieved is None
        print(f"After invalidation {key}: {'SUCCESS' if success else 'FAILED'}")


async def test_tag_based_invalidation():
    """Test tag-based cache invalidation"""
    print("\nTesting tag-based invalidation...")
    
    # Set values with tags
    test_data = [
        ("item1", {"data": "value1"}, ["tag1", "tag2"]),
        ("item2", {"data": "value2"}, ["tag2", "tag3"]),
        ("item3", {"data": "value3"}, ["tag1", "tag3"]),
        ("item4", {"data": "value4"}, ["tag4"])
    ]
    
    for key, value, tags in test_data:
        success = await cache_manager.set(key, value, ttl=120, tags=tags)
        print(f"Set {key} with tags {tags}: {'SUCCESS' if success else 'FAILED'}")
    
    # Invalidate by tag
    invalidated_count = await cache_manager.invalidate_by_tags(["tag2"])
    print(f"Invalidated {invalidated_count} entries with tag 'tag2'")
    
    # Check which items were invalidated (should be item1 and item2)
    expected_results = [
        ("item1", None),  # Should be invalidated (has tag2)
        ("item2", None),  # Should be invalidated (has tag2)
        ("item3", {"data": "value3"}),  # Should remain (no tag2)
        ("item4", {"data": "value4"})   # Should remain (no tag2)
    ]
    
    for key, expected in expected_results:
        retrieved = await cache_manager.get(key)
        success = retrieved == expected
        status = "INVALIDATED" if expected is None else "PRESERVED"
        print(f"Item {key} {status}: {'SUCCESS' if success else 'FAILED'}")


async def test_specialized_cache_methods():
    """Test specialized cache methods for queries and schema"""
    print("\nTesting specialized cache methods...")
    
    # Test query result caching
    query_hash = "test_query_hash_123"
    query_result = {
        "rows": [{"id": 1, "name": "Product 1"}, {"id": 2, "name": "Product 2"}],
        "total": 2,
        "execution_time": 0.15
    }
    tables_used = ["products", "categories"]
    
    success = await cache_manager.cache_query_result(query_hash, query_result, tables_used)
    print(f"Cache query result: {'SUCCESS' if success else 'FAILED'}")
    
    retrieved_result = await cache_manager.get_query_result(query_hash)
    print(f"Get query result: {'SUCCESS' if retrieved_result == query_result else 'FAILED'}")
    
    # Test schema metadata caching
    table_name = "test_table"
    schema_metadata = {
        "columns": ["id", "name", "price"],
        "types": {"id": "integer", "name": "varchar", "price": "decimal"},
        "indexes": ["idx_name", "idx_price"]
    }
    
    success = await cache_manager.cache_schema_metadata(table_name, schema_metadata)
    print(f"Cache schema metadata: {'SUCCESS' if success else 'FAILED'}")
    
    retrieved_schema = await cache_manager.get_schema_metadata(table_name)
    print(f"Get schema metadata: {'SUCCESS' if retrieved_schema == schema_metadata else 'FAILED'}")
    
    # Test table cache invalidation
    invalidated = await cache_manager.invalidate_table_cache("products")
    print(f"Invalidated table cache: {invalidated} entries")


async def test_cache_health_and_stats():
    """Test cache health check and statistics"""
    print("\nTesting cache health and statistics...")
    
    # Health check
    health = await cache_manager.health_check()
    print(f"Cache health check:")
    print(f"  Overall status: {health['overall_status']}")
    print(f"  Memory cache: {health['memory_cache']['status']}")
    print(f"  Redis cache: {health['redis_cache']['status']}")
    
    # Cache statistics
    stats = cache_manager.get_cache_stats()
    print(f"\nCache statistics:")
    print(f"  Memory cache entries: {stats['memory_cache']['total_entries']}")
    print(f"  Redis connected: {stats['redis_connected']}")
    print(f"  Cache hit ratio: {stats['performance']['hit_ratio']:.2%}")
    print(f"  Total hits: {stats['performance']['cache_hits']}")
    print(f"  Total misses: {stats['performance']['cache_misses']}")


async def main():
    """Run all cache tests"""
    print("Starting Redis Cache System Tests")
    print("=" * 50)
    
    try:
        await test_basic_cache_operations()
        await test_namespace_operations()
        await test_tag_based_invalidation()
        await test_specialized_cache_methods()
        await test_cache_health_and_stats()
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())