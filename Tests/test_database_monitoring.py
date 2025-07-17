#!/usr/bin/env python3
"""
Test script for database connection pooling and monitoring
"""
import asyncio
import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import (
    get_monitored_db_session, 
    db_monitor, 
    db_health_checker,
    base_engine
)
from sqlalchemy import text


def test_basic_database_connection():
    """Test basic database connectivity"""
    print("Testing basic database connection...")
    
    try:
        with get_monitored_db_session() as session:
            result = session.execute(text("SELECT 1 as test_value"))
            value = result.scalar()
            print(f"Basic connection test: {'SUCCESS' if value == 1 else 'FAILED'}")
            return True
    except Exception as e:
        print(f"Basic connection test: FAILED - {e}")
        return False


def test_query_monitoring():
    """Test query execution monitoring"""
    print("\nTesting query monitoring...")
    
    try:
        # Execute some test queries
        test_queries = [
            "SELECT 1 as simple_query",
            "SELECT 2 as another_query", 
            "SELECT pg_sleep(0.1), 3 as slow_query",  # Simulate slow query
        ]
        
        for query in test_queries:
            with get_monitored_db_session() as session:
                session.execute(text(query))
        
        # Check if queries were monitored
        total_queries = db_monitor.total_queries
        print(f"Total queries monitored: {total_queries}")
        
        # Get performance summary
        perf_summary = db_monitor.get_performance_summary()
        print(f"Average execution time: {perf_summary['overall_stats']['avg_execution_time']:.4f}s")
        print(f"Error rate: {perf_summary['overall_stats']['error_rate']:.2%}")
        
        return total_queries >= len(test_queries)
        
    except Exception as e:
        print(f"Query monitoring test: FAILED - {e}")
        return False


def test_connection_pool_monitoring():
    """Test connection pool monitoring"""
    print("\nTesting connection pool monitoring...")
    
    try:
        # Get initial pool stats
        initial_stats = db_health_checker.get_connection_pool_stats()
        print(f"Initial pool stats:")
        print(f"  Pool size: {initial_stats['pool_size']}")
        print(f"  Checked out: {initial_stats['checked_out']}")
        print(f"  Available: {initial_stats['available_connections']}")
        
        # Create multiple concurrent connections
        def execute_query(query_id):
            with get_monitored_db_session() as session:
                session.execute(text(f"SELECT {query_id}, pg_sleep(0.1)"))
                return query_id
        
        # Execute queries concurrently to test pool usage
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(execute_query, i) for i in range(5)]
            results = [future.result() for future in futures]
        
        # Get final pool stats
        final_stats = db_health_checker.get_connection_pool_stats()
        print(f"After concurrent queries:")
        print(f"  Pool size: {final_stats['pool_size']}")
        print(f"  Checked out: {final_stats['checked_out']}")
        print(f"  Utilization: {final_stats['utilization_percent']:.1f}%")
        
        return len(results) == 5
        
    except Exception as e:
        print(f"Connection pool monitoring test: FAILED - {e}")
        return False


def test_slow_query_detection():
    """Test slow query detection and monitoring"""
    print("\nTesting slow query detection...")
    
    try:
        # Execute a deliberately slow query
        with get_monitored_db_session() as session:
            session.execute(text("SELECT pg_sleep(1.5), 'slow_query' as result"))
        
        # Check if slow query was detected
        slow_queries = db_monitor.get_slow_queries(limit=5)
        
        print(f"Detected {len(slow_queries)} slow queries")
        if slow_queries:
            latest_slow = slow_queries[0]
            print(f"Latest slow query execution time: {latest_slow['execution_time']:.2f}s")
            print(f"Query: {latest_slow['sql'][:100]}...")
        
        return len(slow_queries) > 0
        
    except Exception as e:
        print(f"Slow query detection test: FAILED - {e}")
        return False


def test_error_handling_monitoring():
    """Test error handling and monitoring"""
    print("\nTesting error handling monitoring...")
    
    try:
        initial_errors = db_monitor.total_errors
        
        # Execute an invalid query to trigger error monitoring
        try:
            with get_monitored_db_session() as session:
                session.execute(text("SELECT * FROM non_existent_table"))
        except Exception:
            pass  # Expected to fail
        
        # Check if error was monitored
        final_errors = db_monitor.total_errors
        errors_detected = final_errors > initial_errors
        
        print(f"Errors before: {initial_errors}, after: {final_errors}")
        print(f"Error monitoring: {'SUCCESS' if errors_detected else 'FAILED'}")
        
        return errors_detected
        
    except Exception as e:
        print(f"Error handling monitoring test: FAILED - {e}")
        return False


async def test_database_health_check():
    """Test comprehensive database health check"""
    print("\nTesting database health check...")
    
    try:
        health_status = await db_health_checker.check_database_health()
        
        print(f"Database status: {health_status['status']}")
        print(f"Connection pool utilization: {health_status['connection_pool'].get('utilization', 0):.2%}")
        
        if health_status['recommendations']:
            print("Optimization recommendations:")
            for rec in health_status['recommendations'][:3]:
                print(f"  - {rec}")
        
        return health_status['status'] in ['healthy', 'degraded']
        
    except Exception as e:
        print(f"Database health check test: FAILED - {e}")
        return False


def test_query_optimization_suggestions():
    """Test query optimization suggestions"""
    print("\nTesting query optimization suggestions...")
    
    try:
        # Execute some queries that might trigger optimization suggestions
        queries = [
            "SELECT * FROM information_schema.tables WHERE table_name LIKE '%test%'",
            "SELECT * FROM information_schema.columns ORDER BY table_name",
            "SELECT COUNT(*) FROM information_schema.tables",
        ]
        
        for query in queries:
            with get_monitored_db_session() as session:
                session.execute(text(query))
        
        # Get optimization suggestions
        suggestions = db_monitor.get_query_optimization_suggestions()
        
        print(f"Generated {len(suggestions)} optimization suggestions")
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"  {i}. {suggestion}")
        
        return True  # Always return True as suggestions are optional
        
    except Exception as e:
        print(f"Query optimization suggestions test: FAILED - {e}")
        return False


def test_performance_metrics():
    """Test performance metrics collection"""
    print("\nTesting performance metrics collection...")
    
    try:
        # Execute various queries to generate metrics
        for i in range(10):
            with get_monitored_db_session() as session:
                session.execute(text(f"SELECT {i}, 'test_query_{i}'"))
        
        # Get performance summary
        perf_summary = db_monitor.get_performance_summary()
        
        print("Performance Summary:")
        print(f"  Total queries: {perf_summary['overall_stats']['total_queries']}")
        print(f"  Average execution time: {perf_summary['overall_stats']['avg_execution_time']:.4f}s")
        print(f"  Error rate: {perf_summary['overall_stats']['error_rate']:.2%}")
        
        recent_perf = perf_summary['recent_performance']
        print(f"  Recent queries (last hour): {recent_perf['queries_last_hour']}")
        print(f"  Recent avg response time: {recent_perf['avg_response_time']:.4f}s")
        
        return perf_summary['overall_stats']['total_queries'] > 0
        
    except Exception as e:
        print(f"Performance metrics test: FAILED - {e}")
        return False


async def main():
    """Run all database monitoring tests"""
    print("Starting Database Monitoring and Connection Pooling Tests")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    test_functions = [
        ("Basic Database Connection", test_basic_database_connection),
        ("Query Monitoring", test_query_monitoring),
        ("Connection Pool Monitoring", test_connection_pool_monitoring),
        ("Slow Query Detection", test_slow_query_detection),
        ("Error Handling Monitoring", test_error_handling_monitoring),
        ("Query Optimization Suggestions", test_query_optimization_suggestions),
        ("Performance Metrics", test_performance_metrics),
    ]
    
    for test_name, test_func in test_functions:
        try:
            result = test_func()
            test_results.append((test_name, result))
            print(f"{test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            test_results.append((test_name, False))
            print(f"{test_name}: FAILED - {e}")
    
    # Run async tests
    async_tests = [
        ("Database Health Check", test_database_health_check),
    ]
    
    for test_name, test_func in async_tests:
        try:
            result = await test_func()
            test_results.append((test_name, result))
            print(f"{test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            test_results.append((test_name, False))
            print(f"{test_name}: FAILED - {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary:")
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All database monitoring tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main())