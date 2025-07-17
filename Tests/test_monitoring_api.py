#!/usr/bin/env python3
"""
Test script for monitoring API endpoints
"""
import asyncio
import sys
import os
import json
from fastapi.testclient import TestClient

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import after path setup
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test the system health endpoint"""
    print("Testing /api/v1/monitoring/health endpoint...")
    
    try:
        response = client.get("/api/v1/monitoring/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Health Status: {data.get('status', 'unknown')}")
            print(f"Database Status: {data.get('components', {}).get('database', {}).get('status', 'unknown')}")
            print(f"Cache Status: {data.get('components', {}).get('cache', {}).get('status', 'unknown')}")
            return True
        else:
            print(f"Health endpoint failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Health endpoint test failed: {e}")
        return False


def test_database_performance_endpoint():
    """Test the database performance endpoint"""
    print("\nTesting /api/v1/monitoring/database/performance endpoint...")
    
    try:
        response = client.get("/api/v1/monitoring/database/performance")
        
        if response.status_code == 200:
            data = response.json()
            perf_metrics = data.get('performance_metrics', {}).get('overall_stats', {})
            
            print(f"Total Queries: {perf_metrics.get('total_queries', 0)}")
            print(f"Error Rate: {perf_metrics.get('error_rate', 0):.2%}")
            print(f"Avg Execution Time: {perf_metrics.get('avg_execution_time', 0):.4f}s")
            
            pool_stats = data.get('connection_pool', {})
            print(f"Pool Utilization: {pool_stats.get('utilization_percent', 0):.1f}%")
            
            return True
        else:
            print(f"Database performance endpoint failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Database performance endpoint test failed: {e}")
        return False


def test_cache_stats_endpoint():
    """Test the cache statistics endpoint"""
    print("\nTesting /api/v1/monitoring/cache/stats endpoint...")
    
    try:
        response = client.get("/api/v1/monitoring/cache/stats")
        
        if response.status_code == 200:
            data = response.json()
            cache_stats = data.get('cache_statistics', {}).get('performance', {})
            
            print(f"Cache Hit Ratio: {cache_stats.get('hit_ratio', 0):.2%}")
            print(f"Total Hits: {cache_stats.get('cache_hits', 0)}")
            print(f"Total Misses: {cache_stats.get('cache_misses', 0)}")
            
            health_status = data.get('health_status', {})
            print(f"Overall Cache Status: {health_status.get('overall_status', 'unknown')}")
            
            return True
        else:
            print(f"Cache stats endpoint failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Cache stats endpoint test failed: {e}")
        return False


def test_metrics_summary_endpoint():
    """Test the metrics summary endpoint"""
    print("\nTesting /api/v1/monitoring/metrics/summary endpoint...")
    
    try:
        response = client.get("/api/v1/monitoring/metrics/summary")
        
        if response.status_code == 200:
            data = response.json()
            summary = data.get('summary', {})
            
            print(f"System Efficiency Score: {summary.get('system_efficiency_score', 0)}")
            print(f"Total Database Queries: {summary.get('total_database_queries', 0)}")
            print(f"Cache Hit Ratio: {summary.get('cache_hit_ratio', 0):.2%}")
            print(f"Connection Pool Utilization: {summary.get('connection_pool_utilization', 0):.2%}")
            
            recommendations = data.get('recommendations', {}).get('database', [])
            if recommendations:
                print(f"Database Recommendations: {len(recommendations)}")
                for i, rec in enumerate(recommendations[:2], 1):
                    print(f"  {i}. {rec[:80]}...")
            
            return True
        else:
            print(f"Metrics summary endpoint failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Metrics summary endpoint test failed: {e}")
        return False


def test_realtime_metrics_endpoint():
    """Test the real-time metrics endpoint"""
    print("\nTesting /api/v1/monitoring/metrics/realtime endpoint...")
    
    try:
        response = client.get("/api/v1/monitoring/metrics/realtime")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"Timestamp: {data.get('timestamp', 'unknown')}")
            print(f"Interval: {data.get('interval_minutes', 0)} minutes")
            
            db_metrics = data.get('database', {})
            print(f"Queries per minute: {db_metrics.get('queries_per_minute', 0):.2f}")
            print(f"Active connections: {db_metrics.get('active_connections', 0)}")
            
            cache_metrics = data.get('cache', {})
            print(f"Cache hit ratio: {cache_metrics.get('hit_ratio', 0):.2%}")
            print(f"Memory cache entries: {cache_metrics.get('memory_cache_entries', 0)}")
            
            return True
        else:
            print(f"Real-time metrics endpoint failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Real-time metrics endpoint test failed: {e}")
        return False


def test_slow_queries_endpoint():
    """Test the slow queries endpoint"""
    print("\nTesting /api/v1/monitoring/database/slow-queries endpoint...")
    
    try:
        response = client.get("/api/v1/monitoring/database/slow-queries?limit=5")
        
        if response.status_code == 200:
            data = response.json()
            
            slow_queries = data.get('slow_queries', [])
            print(f"Slow queries found: {len(slow_queries)}")
            print(f"Threshold: {data.get('threshold_seconds', 0)}s")
            
            if slow_queries:
                for i, query in enumerate(slow_queries[:2], 1):
                    print(f"  {i}. {query.get('execution_time', 0):.2f}s - {query.get('sql', '')[:60]}...")
            
            return True
        else:
            print(f"Slow queries endpoint failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Slow queries endpoint test failed: {e}")
        return False


def generate_some_activity():
    """Generate some database activity to test monitoring"""
    print("\nGenerating database activity for monitoring...")
    
    try:
        # Make some API calls to generate database activity
        test_endpoints = [
            "/api/v1/monitoring/health",
            "/api/v1/monitoring/database/performance",
            "/api/v1/monitoring/cache/stats"
        ]
        
        for endpoint in test_endpoints:
            for _ in range(3):
                response = client.get(endpoint)
                if response.status_code != 200:
                    print(f"Failed to call {endpoint}: {response.status_code}")
        
        print("Generated database activity successfully")
        return True
        
    except Exception as e:
        print(f"Failed to generate activity: {e}")
        return False


def main():
    """Run all monitoring API tests"""
    print("Starting Monitoring API Tests")
    print("=" * 50)
    
    # Generate some activity first
    generate_some_activity()
    
    test_functions = [
        ("Health Endpoint", test_health_endpoint),
        ("Database Performance Endpoint", test_database_performance_endpoint),
        ("Cache Stats Endpoint", test_cache_stats_endpoint),
        ("Metrics Summary Endpoint", test_metrics_summary_endpoint),
        ("Real-time Metrics Endpoint", test_realtime_metrics_endpoint),
        ("Slow Queries Endpoint", test_slow_queries_endpoint),
    ]
    
    results = []
    
    for test_name, test_func in test_functions:
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            results.append((test_name, False))
            print(f"{test_name}: FAILED - {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All monitoring API tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    main()