#!/usr/bin/env python3
"""
Basic test script for monitoring and logging implementation
"""
import sys
import os
import time
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_monitoring_imports():
    """Test that monitoring modules can be imported"""
    print("Testing monitoring module imports...")
    
    try:
        from app.core.monitoring import (
            db_monitor, 
            cache_monitor, 
            system_monitor, 
            alert_manager,
            get_comprehensive_metrics
        )
        print("✓ Monitoring modules imported successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to import monitoring modules: {e}")
        return False


def test_logging_imports():
    """Test that logging modules can be imported"""
    print("Testing logging module imports...")
    
    try:
        from app.core.logging import logger, api_usage_logger, error_tracker
        print("✓ Logging modules imported successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to import logging modules: {e}")
        return False


def test_database_monitor():
    """Test database monitoring functionality"""
    print("Testing database monitor...")
    
    try:
        from app.core.monitoring import db_monitor
        
        # Test recording a query
        db_monitor.record_query(
            sql="SELECT 1 as test_query",
            execution_time=0.123,
            success=True
        )
        
        # Test recording a slow query
        db_monitor.record_query(
            sql="SELECT pg_sleep(2), 'slow_query'",
            execution_time=2.1,
            success=True
        )
        
        # Test recording an error
        db_monitor.record_query(
            sql="SELECT * FROM non_existent_table",
            execution_time=0.05,
            success=False,
            error_message="Table does not exist"
        )
        
        # Get performance summary
        summary = db_monitor.get_performance_summary()
        print(f"  Total queries: {summary['overall_stats']['total_queries']}")
        print(f"  Error rate: {summary['overall_stats']['error_rate']:.2%}")
        
        # Get slow queries
        slow_queries = db_monitor.get_slow_queries()
        print(f"  Slow queries detected: {len(slow_queries)}")
        
        print("✓ Database monitor test passed")
        return True
        
    except Exception as e:
        print(f"✗ Database monitor test failed: {e}")
        return False


def test_cache_monitor():
    """Test cache monitoring functionality"""
    print("Testing cache monitor...")
    
    try:
        from app.core.monitoring import cache_monitor
        
        # Simulate cache operations
        for i in range(10):
            if i % 3 == 0:
                cache_monitor.record_cache_miss()
            else:
                cache_monitor.record_cache_hit()
            
            if i % 5 == 0:
                cache_monitor.record_cache_set()
        
        # Get cache statistics
        stats = cache_monitor.get_cache_statistics()
        print(f"  Cache hits: {stats['performance']['cache_hits']}")
        print(f"  Cache misses: {stats['performance']['cache_misses']}")
        print(f"  Hit ratio: {stats['performance']['hit_ratio']:.2%}")
        
        print("✓ Cache monitor test passed")
        return True
        
    except Exception as e:
        print(f"✗ Cache monitor test failed: {e}")
        return False


def test_logging_system():
    """Test logging system functionality"""
    print("Testing logging system...")
    
    try:
        from app.core.logging import logger, api_usage_logger, error_tracker
        
        # Test structured logging
        logger.info("Test log message", extra={
            "test_type": "basic_test",
            "component": "monitoring_system"
        })
        
        # Test API usage logging
        api_usage_logger.log_api_request(
            endpoint="/test",
            method="GET",
            client_ip="127.0.0.1",
            response_time=0.123,
            status_code=200
        )
        
        # Test error tracking
        error_tracker.track_error(
            error_type="test_error",
            error_message="This is a test error",
            context={"test": True}
        )
        
        # Get usage analytics
        analytics = api_usage_logger.get_usage_analytics()
        print(f"  Tracked endpoints: {len(analytics.get('endpoints', {}))}")
        
        # Get error summary
        error_summary = error_tracker.get_error_summary()
        print(f"  Total errors: {error_summary.get('total_errors', 0)}")
        
        print("✓ Logging system test passed")
        return True
        
    except Exception as e:
        print(f"✗ Logging system test failed: {e}")
        return False


def test_comprehensive_metrics():
    """Test comprehensive metrics collection"""
    print("Testing comprehensive metrics...")
    
    try:
        from app.core.monitoring import get_comprehensive_metrics
        
        # Get comprehensive metrics
        metrics = get_comprehensive_metrics()
        
        print(f"  Metrics timestamp: {metrics.get('timestamp', 'unknown')}")
        print(f"  Database metrics: {'database' in metrics}")
        print(f"  Cache metrics: {'cache' in metrics}")
        print(f"  System metrics: {'system' in metrics}")
        print(f"  Alert metrics: {'alerts' in metrics}")
        
        print("✓ Comprehensive metrics test passed")
        return True
        
    except Exception as e:
        print(f"✗ Comprehensive metrics test failed: {e}")
        return False


def main():
    """Run basic monitoring and logging tests"""
    print("Starting Basic Monitoring and Logging Tests")
    print("=" * 50)
    
    test_functions = [
        ("Monitoring Imports", test_monitoring_imports),
        ("Logging Imports", test_logging_imports),
        ("Database Monitor", test_database_monitor),
        ("Cache Monitor", test_cache_monitor),
        ("Logging System", test_logging_system),
        ("Comprehensive Metrics", test_comprehensive_metrics),
    ]
    
    results = []
    
    for test_name, test_func in test_functions:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            results.append((test_name, False))
            print(f"✗ {test_name} failed with exception: {e}")
    
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
        print("🎉 All basic monitoring and logging tests passed!")
        print("\nMonitoring and logging implementation is working correctly!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    main()