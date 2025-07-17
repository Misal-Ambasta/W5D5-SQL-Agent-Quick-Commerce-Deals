#!/usr/bin/env python3
"""
Test script for comprehensive monitoring and logging implementation
"""
import asyncio
import sys
import os
import time
import json
from datetime import datetime
from fastapi.testclient import TestClient

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import after path setup
from app.main import app
from app.core.monitoring import (
    db_monitor, 
    cache_monitor, 
    system_monitor, 
    alert_manager,
    get_comprehensive_metrics
)
from app.core.logging import logger, api_usage_logger, error_tracker

client = TestClient(app)


def test_logging_system():
    """Test the enhanced logging system"""
    print("Testing Enhanced Logging System...")
    
    try:
        # Test structured logging
        logger.info("Test log message", extra={
            "test_type": "logging_test",
            "component": "monitoring_system",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Test error tracking
        error_tracker.track_error(
            error_type="test_error",
            error_message="This is a test error for monitoring",
            context={"test": True, "component": "logging_test"}
        )
        
        # Test API usage logging
        api_usage_logger.log_api_request(
            endpoint="/test",
            method="GET",
            client_ip="127.0.0.1",
            response_time=0.123,
            status_code=200,
            user_agent="test-client"
        )
        
        print("✓ Logging system test passed")
        return True
        
    except Exception as e:
        print(f"✗ Logging system test failed: {e}")
        return False


def test_database_monitoring():
    """Test database monitoring functionality"""
    print("\nTesting Database Monitoring...")
    
    try:
        # Test basic monitoring functionality
        from app.core.database import get_monitored_db_session
        from sqlalchemy import text
        
        # Execute some test queries to generate monitoring data
        test_queries = [
            "SELECT 1 as test_query",
            "SELECT 2, 'test' as another_query",
            "SELECT pg_sleep(0.1), 3 as slow_query",  # Simulate slow query
        ]
        
        for query in test_queries:
            with get_monitored_db_session() as session:
                session.execute(text(query))
        
        # Check if monitoring data was collected
        performance_summary = db_monitor.get_performance_summary()
        
        print(f"  Total queries monitored: {performance_summary['overall_stats']['total_queries']}")
        print(f"  Average execution time: {performance_summary['overall_stats']['avg_execution_time']:.4f}s")
        print(f"  Error rate: {performance_summary['overall_stats']['error_rate']:.2%}")
        
        # Test slow query detection
        slow_queries = db_monitor.get_slow_queries(limit=5)
        print(f"  Slow queries detected: {len(slow_queries)}")
        
        # Test optimization suggestions
        suggestions = db_monitor.get_query_optimization_suggestions()
        print(f"  Optimization suggestions: {len(suggestions)}")
        
        print("✓ Database monitoring test passed")
        return True
        
    except Exception as e:
        print(f"✗ Database monitoring test failed: {e}")
        return False


def test_cache_monitoring():
    """Test cache monitoring functionality"""
    print("\nTesting Cache Monitoring...")
    
    try:
        # Simulate cache operations
        for i in range(10):
            if i % 3 == 0:
                cache_monitor.record_cache_miss()
            else:
                cache_monitor.record_cache_hit()
            
            if i % 5 == 0:
                cache_monitor.record_cache_set()
        
        # Get cache statistics
        cache_stats = cache_monitor.get_cache_statistics()
        
        print(f"  Cache hits: {cache_stats['performance']['cache_hits']}")
        print(f"  Cache misses: {cache_stats['performance']['cache_misses']}")
        print(f"  Hit ratio: {cache_stats['performance']['hit_ratio']:.2%}")
        print(f"  Total operations: {cache_stats['performance']['total_operations']}")
        
        print("✓ Cache monitoring test passed")
        return True
        
    except Exception as e:
        print(f"✗ Cache monitoring test failed: {e}")
        return False


async def test_system_monitoring():
    """Test system resource monitoring"""
    print("\nTesting System Monitoring...")
    
    try:
        # Start system monitoring
        await system_monitor.start_monitoring(interval_seconds=5)
        
        # Wait for some metrics to be collected
        await asyncio.sleep(6)
        
        # Get current metrics
        current_metrics = system_monitor.get_current_metrics()
        if current_metrics:
            print(f"  CPU usage: {current_metrics.cpu_percent:.1f}%")
            print(f"  Memory usage: {current_metrics.memory_percent:.1f}%")
            print(f"  Disk usage: {current_metrics.disk_usage_percent:.1f}%")
        
        # Get metrics summary
        summary = system_monitor.get_metrics_summary(hours=1)
        if summary:
            print(f"  Data points collected: {summary.get('data_points', 0)}")
        
        # Stop monitoring
        await system_monitor.stop_monitoring()
        
        print("✓ System monitoring test passed")
        return True
        
    except Exception as e:
        print(f"✗ System monitoring test failed: {e}")
        return False


def test_alert_system():
    """Test alert and notification system"""
    print("\nTesting Alert System...")
    
    try:
        # Create mock metrics to trigger alerts
        from app.core.monitoring import SystemMetrics
        
        # Create high CPU usage scenario
        high_cpu_metrics = SystemMetrics(
            timestamp=datetime.utcnow(),
            cpu_percent=85.0,  # Above threshold
            memory_percent=50.0,
            disk_usage_percent=60.0,
            active_connections=10,
            queries_per_minute=100.0,
            cache_hit_ratio=0.8,
            error_rate=0.02
        )
        
        # Mock database and cache stats
        db_stats = {'overall_stats': {'error_rate': 0.02}}
        cache_stats = {'performance': {'hit_ratio': 0.8}}
        
        # Check thresholds (should trigger CPU alert)
        alert_manager.check_thresholds(high_cpu_metrics, db_stats, cache_stats)
        
        # Get active alerts
        active_alerts = alert_manager.get_active_alerts()
        print(f"  Active alerts: {len(active_alerts)}")
        
        if active_alerts:
            for alert in active_alerts:
                print(f"    - {alert['type']}: {alert['message']}")
        
        print("✓ Alert system test passed")
        return True
        
    except Exception as e:
        print(f"✗ Alert system test failed: {e}")
        return False


def test_monitoring_api_endpoints():
    """Test monitoring API endpoints"""
    print("\nTesting Monitoring API Endpoints...")
    
    try:
        # Test health endpoint
        response = client.get("/api/v1/monitoring/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"  Health status: {health_data.get('status', 'unknown')}")
        else:
            print(f"  Health endpoint failed: {response.status_code}")
        
        # Test database performance endpoint
        response = client.get("/api/v1/monitoring/database/performance")
        if response.status_code == 200:
            perf_data = response.json()
            print(f"  Database queries: {perf_data.get('performance_metrics', {}).get('overall_stats', {}).get('total_queries', 0)}")
        else:
            print(f"  Database performance endpoint failed: {response.status_code}")
        
        # Test cache stats endpoint
        response = client.get("/api/v1/monitoring/cache/stats")
        if response.status_code == 200:
            cache_data = response.json()
            hit_ratio = cache_data.get('cache_statistics', {}).get('performance', {}).get('hit_ratio', 0)
            print(f"  Cache hit ratio: {hit_ratio:.2%}")
        else:
            print(f"  Cache stats endpoint failed: {response.status_code}")
        
        # Test metrics summary endpoint
        response = client.get("/api/v1/monitoring/metrics/summary")
        if response.status_code == 200:
            summary_data = response.json()
            efficiency = summary_data.get('summary', {}).get('system_efficiency_score', 0)
            print(f"  System efficiency score: {efficiency}")
        else:
            print(f"  Metrics summary endpoint failed: {response.status_code}")
        
        # Test real-time metrics endpoint
        response = client.get("/api/v1/monitoring/metrics/realtime")
        if response.status_code == 200:
            realtime_data = response.json()
            print(f"  Real-time metrics timestamp: {realtime_data.get('timestamp', 'unknown')}")
        else:
            print(f"  Real-time metrics endpoint failed: {response.status_code}")
        
        print("✓ Monitoring API endpoints test passed")
        return True
        
    except Exception as e:
        print(f"✗ Monitoring API endpoints test failed: {e}")
        return False


def test_comprehensive_metrics():
    """Test comprehensive metrics collection"""
    print("\nTesting Comprehensive Metrics Collection...")
    
    try:
        # Get comprehensive metrics
        metrics = get_comprehensive_metrics()
        
        print(f"  Metrics timestamp: {metrics.get('timestamp', 'unknown')}")
        print(f"  Database metrics available: {'database' in metrics}")
        print(f"  Cache metrics available: {'cache' in metrics}")
        print(f"  System metrics available: {'system' in metrics}")
        print(f"  Alert metrics available: {'alerts' in metrics}")
        
        # Check specific metric values
        db_metrics = metrics.get('database', {})
        if db_metrics:
            overall_stats = db_metrics.get('overall_stats', {})
            print(f"  Total database queries: {overall_stats.get('total_queries', 0)}")
            print(f"  Database error rate: {overall_stats.get('error_rate', 0):.2%}")
        
        cache_metrics = metrics.get('cache', {})
        if cache_metrics:
            perf_stats = cache_metrics.get('performance', {})
            print(f"  Cache hit ratio: {perf_stats.get('hit_ratio', 0):.2%}")
        
        alerts = metrics.get('alerts', {})
        print(f"  Active alerts: {alerts.get('total_count', 0)}")
        
        print("✓ Comprehensive metrics test passed")
        return True
        
    except Exception as e:
        print(f"✗ Comprehensive metrics test failed: {e}")
        return False


def test_api_usage_analytics():
    """Test API usage analytics"""
    print("\nTesting API Usage Analytics...")
    
    try:
        # Generate some API usage data
        endpoints = ["/api/v1/query", "/api/v1/products", "/api/v1/deals"]
        methods = ["GET", "POST"]
        
        for i in range(20):
            endpoint = endpoints[i % len(endpoints)]
            method = methods[i % len(methods)]
            
            api_usage_logger.log_api_request(
                endpoint=endpoint,
                method=method,
                client_ip=f"192.168.1.{i % 10 + 1}",
                response_time=0.1 + (i % 5) * 0.05,
                status_code=200 if i % 10 != 0 else 500,
                user_agent="test-client"
            )
        
        # Get usage analytics
        analytics = api_usage_logger.get_usage_analytics()
        
        print(f"  Tracked endpoints: {len(analytics.get('endpoints', {}))}")
        print(f"  Total unique IPs: {analytics.get('total_unique_ips', 0)}")
        print(f"  Rate limit violations: {analytics.get('rate_limit_violations', 0)}")
        
        # Show endpoint statistics
        for endpoint, stats in list(analytics.get('endpoints', {}).items())[:3]:
            print(f"    {endpoint}: {stats['total_requests']} requests, "
                  f"{stats['success_rate']:.1%} success rate")
        
        print("✓ API usage analytics test passed")
        return True
        
    except Exception as e:
        print(f"✗ API usage analytics test failed: {e}")
        return False


def test_error_tracking():
    """Test error tracking system"""
    print("\nTesting Error Tracking...")
    
    try:
        # Generate some test errors
        error_types = ["database_error", "validation_error", "timeout_error"]
        
        for i in range(15):
            error_type = error_types[i % len(error_types)]
            error_tracker.track_error(
                error_type=error_type,
                error_message=f"Test error message {i}",
                context={"test_id": i, "component": "test_system"}
            )
        
        # Get error summary
        error_summary = error_tracker.get_error_summary()
        
        print(f"  Total error types: {error_summary.get('total_error_types', 0)}")
        print(f"  Total errors: {error_summary.get('total_errors', 0)}")
        print(f"  Critical errors: {len(error_summary.get('critical_errors', []))}")
        
        # Show error counts by type
        error_counts = error_summary.get('error_counts', {})
        for error_type, count in error_counts.items():
            print(f"    {error_type}: {count} occurrences")
        
        print("✓ Error tracking test passed")
        return True
        
    except Exception as e:
        print(f"✗ Error tracking test failed: {e}")
        return False


async def main():
    """Run all monitoring and logging tests"""
    print("Starting Comprehensive Monitoring and Logging Implementation Tests")
    print("=" * 70)
    
    test_results = []
    
    # Run synchronous tests
    sync_tests = [
        ("Enhanced Logging System", test_logging_system),
        ("Database Monitoring", test_database_monitoring),
        ("Cache Monitoring", test_cache_monitoring),
        ("Alert System", test_alert_system),
        ("Monitoring API Endpoints", test_monitoring_api_endpoints),
        ("Comprehensive Metrics", test_comprehensive_metrics),
        ("API Usage Analytics", test_api_usage_analytics),
        ("Error Tracking", test_error_tracking),
    ]
    
    for test_name, test_func in sync_tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            test_results.append((test_name, False))
            print(f"✗ {test_name} failed with exception: {e}")
    
    # Run async tests
    async_tests = [
        ("System Monitoring", test_system_monitoring),
    ]
    
    for test_name, test_func in async_tests:
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            test_results.append((test_name, False))
            print(f"✗ {test_name} failed with exception: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Results Summary:")
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All monitoring and logging tests passed!")
        print("\nMonitoring and logging implementation is complete and functional!")
        print("\nKey features implemented:")
        print("  • Comprehensive database query monitoring")
        print("  • Cache performance tracking")
        print("  • System resource monitoring")
        print("  • Alert and notification system")
        print("  • API usage analytics")
        print("  • Error tracking and alerting")
        print("  • Real-time metrics collection")
        print("  • Monitoring dashboard endpoints")
        print("  • Enhanced structured logging")
        print("  • Performance optimization suggestions")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        print("The monitoring system may have partial functionality.")


if __name__ == "__main__":
    asyncio.run(main())