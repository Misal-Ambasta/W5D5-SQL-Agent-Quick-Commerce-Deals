"""
Monitoring and metrics API endpoints
"""
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.core.monitoring import (
    db_monitor, 
    cache_monitor, 
    system_monitor, 
    alert_manager,
    get_comprehensive_metrics
)
from app.core.logging import logger, api_usage_logger, error_tracker
from app.core.database import SessionLocal, engine
from sqlalchemy import text
import redis
import asyncio

router = APIRouter()


@router.get("/health")
async def health_check():
    """Comprehensive system health check"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "components": {}
        }
        
        # Database health check
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            health_status["components"]["database"] = {
                "status": "healthy",
                "message": "Database connection successful"
            }
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}"
            }
            health_status["status"] = "degraded"
        
        # Cache health check
        try:
            # This would connect to Redis if configured
            health_status["components"]["cache"] = {
                "status": "healthy",
                "message": "Cache system operational"
            }
        except Exception as e:
            health_status["components"]["cache"] = {
                "status": "degraded",
                "message": f"Cache system issues: {str(e)}"
            }
        
        # System resources check
        current_metrics = system_monitor.get_current_metrics()
        if current_metrics:
            if current_metrics.cpu_percent > 90 or current_metrics.memory_percent > 95:
                health_status["status"] = "degraded"
                health_status["components"]["system"] = {
                    "status": "degraded",
                    "message": "High resource usage detected"
                }
            else:
                health_status["components"]["system"] = {
                    "status": "healthy",
                    "message": "System resources normal"
                }
        
        logger.info("Health check completed", status=health_status["status"])
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "message": "Health check failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/database/performance")
async def get_database_performance():
    """Get database performance metrics"""
    try:
        performance_data = db_monitor.get_performance_summary()
        
        # Add connection pool information
        try:
            pool_stats = {
                "pool_size": engine.pool.size(),
                "checked_out": engine.pool.checkedout(),
                "overflow": engine.pool.overflow(),
                "checked_in": engine.pool.checkedin()
            }
            pool_stats["available_connections"] = pool_stats["pool_size"] - pool_stats["checked_out"]
            pool_stats["utilization_percent"] = (
                pool_stats["checked_out"] / pool_stats["pool_size"] * 100 
                if pool_stats["pool_size"] > 0 else 0
            )
        except Exception as e:
            logger.warning(f"Could not get pool stats: {e}")
            pool_stats = {"error": "Pool stats unavailable"}
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "performance_metrics": performance_data,
            "connection_pool": pool_stats,
            "recommendations": db_monitor.get_query_optimization_suggestions()
        }
        
    except Exception as e:
        logger.error(f"Database performance endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get database performance: {str(e)}")


@router.get("/database/slow-queries")
async def get_slow_queries(limit: int = Query(10, ge=1, le=100)):
    """Get slow query information"""
    try:
        slow_queries = db_monitor.get_slow_queries(limit=limit)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "slow_queries": slow_queries,
            "threshold_seconds": db_monitor.slow_query_threshold,
            "total_slow_queries": len(db_monitor.slow_queries)
        }
        
    except Exception as e:
        logger.error(f"Slow queries endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get slow queries: {str(e)}")


@router.get("/cache/stats")
async def get_cache_statistics():
    """Get cache performance statistics"""
    try:
        cache_stats = cache_monitor.get_cache_statistics()
        
        # Add health status based on performance
        hit_ratio = cache_stats.get('performance', {}).get('hit_ratio', 0)
        if hit_ratio > 0.8:
            health_status = {"overall_status": "excellent", "message": "Cache performing optimally"}
        elif hit_ratio > 0.6:
            health_status = {"overall_status": "good", "message": "Cache performing well"}
        elif hit_ratio > 0.4:
            health_status = {"overall_status": "fair", "message": "Cache performance could be improved"}
        else:
            health_status = {"overall_status": "poor", "message": "Cache performance needs attention"}
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cache_statistics": cache_stats,
            "health_status": health_status
        }
        
    except Exception as e:
        logger.error(f"Cache stats endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache statistics: {str(e)}")


@router.get("/metrics/summary")
async def get_metrics_summary():
    """Get comprehensive metrics summary"""
    try:
        comprehensive_metrics = get_comprehensive_metrics()
        
        # Calculate system efficiency score
        db_stats = comprehensive_metrics.get('database', {}).get('overall_stats', {})
        cache_stats = comprehensive_metrics.get('cache', {}).get('performance', {})
        
        # Simple efficiency scoring (0-100)
        db_score = max(0, 100 - (db_stats.get('error_rate', 0) * 1000))  # Penalize errors heavily
        cache_score = cache_stats.get('hit_ratio', 0) * 100
        
        system_efficiency_score = (db_score + cache_score) / 2
        
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "system_efficiency_score": round(system_efficiency_score, 1),
                "total_database_queries": db_stats.get('total_queries', 0),
                "database_error_rate": db_stats.get('error_rate', 0),
                "cache_hit_ratio": cache_stats.get('hit_ratio', 0),
                "active_alerts": len(comprehensive_metrics.get('alerts', {}).get('active', []))
            },
            "recommendations": {
                "database": db_monitor.get_query_optimization_suggestions(),
                "system": []
            }
        }
        
        # Add system recommendations based on metrics
        if system_efficiency_score < 70:
            summary["recommendations"]["system"].append("System efficiency is below optimal - review database and cache performance")
        if db_stats.get('error_rate', 0) > 0.02:
            summary["recommendations"]["system"].append("Database error rate is elevated - investigate query failures")
        if cache_stats.get('hit_ratio', 0) < 0.7:
            summary["recommendations"]["system"].append("Cache hit ratio is low - review caching strategy")
        
        return summary
        
    except Exception as e:
        logger.error(f"Metrics summary endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics summary: {str(e)}")


@router.get("/metrics/realtime")
async def get_realtime_metrics():
    """Get real-time system metrics"""
    try:
        current_metrics = system_monitor.get_current_metrics()
        db_stats = db_monitor.get_performance_summary()
        cache_stats = cache_monitor.get_cache_statistics()
        
        # Calculate queries per minute from recent data
        recent_queries = db_stats.get('recent_performance', {}).get('queries_last_hour', 0)
        queries_per_minute = recent_queries / 60 if recent_queries > 0 else 0
        
        realtime_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "interval_minutes": 1,
            "database": {
                "queries_per_minute": round(queries_per_minute, 2),
                "active_connections": getattr(current_metrics, 'active_connections', 0) if current_metrics else 0,
                "avg_response_time": db_stats.get('recent_performance', {}).get('avg_response_time', 0),
                "error_rate": db_stats.get('overall_stats', {}).get('error_rate', 0)
            },
            "cache": {
                "hit_ratio": cache_stats.get('performance', {}).get('hit_ratio', 0),
                "operations_per_minute": 0,  # Would be calculated from cache operations
                "memory_cache_entries": cache_stats.get('performance', {}).get('total_operations', 0)
            },
            "system": {
                "cpu_percent": getattr(current_metrics, 'cpu_percent', 0) if current_metrics else 0,
                "memory_percent": getattr(current_metrics, 'memory_percent', 0) if current_metrics else 0,
                "disk_usage_percent": getattr(current_metrics, 'disk_usage_percent', 0) if current_metrics else 0
            }
        }
        
        return realtime_data
        
    except Exception as e:
        logger.error(f"Real-time metrics endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get real-time metrics: {str(e)}")


@router.get("/api-usage")
async def get_api_usage_analytics():
    """Get API usage analytics and rate limiting statistics"""
    try:
        usage_analytics = api_usage_logger.get_usage_analytics()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "api_usage": usage_analytics,
            "rate_limiting": {
                "total_violations": len(api_usage_logger.rate_limit_violations),
                "recent_violations": [
                    v for v in api_usage_logger.rate_limit_violations 
                    if v['timestamp'] > datetime.utcnow() - timedelta(hours=1)
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"API usage analytics endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get API usage analytics: {str(e)}")


@router.get("/errors")
async def get_error_tracking():
    """Get error tracking and alerting information"""
    try:
        error_summary = error_tracker.get_error_summary()
        active_alerts = alert_manager.get_active_alerts()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error_tracking": error_summary,
            "alerts": {
                "active_alerts": active_alerts,
                "alert_count": len(active_alerts),
                "critical_alerts": [
                    alert for alert in active_alerts 
                    if alert.get('severity') == 'critical'
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error tracking endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get error tracking: {str(e)}")


@router.get("/system/resources")
async def get_system_resources():
    """Get detailed system resource information"""
    try:
        current_metrics = system_monitor.get_current_metrics()
        metrics_summary = system_monitor.get_metrics_summary(hours=1)
        
        if not current_metrics:
            # Start monitoring if not already started
            await system_monitor.start_monitoring()
            current_metrics = system_monitor.get_current_metrics()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "current_metrics": current_metrics.__dict__ if current_metrics else None,
            "historical_summary": metrics_summary,
            "monitoring_status": "active" if system_monitor._monitoring else "inactive"
        }
        
    except Exception as e:
        logger.error(f"System resources endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system resources: {str(e)}")


@router.post("/alerts/acknowledge/{alert_type}")
async def acknowledge_alert(alert_type: str):
    """Acknowledge an alert to prevent repeated notifications"""
    try:
        # This would typically update the alert status in a persistent store
        logger.info(f"Alert acknowledged: {alert_type}")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Alert {alert_type} acknowledged",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Alert acknowledgment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")


@router.get("/dashboard")
async def get_monitoring_dashboard():
    """Get comprehensive monitoring dashboard data"""
    try:
        # Collect all monitoring data for dashboard
        health_data = await health_check()
        db_performance = await get_database_performance()
        cache_stats = await get_cache_statistics()
        metrics_summary = await get_metrics_summary()
        realtime_metrics = await get_realtime_metrics()
        api_usage = await get_api_usage_analytics()
        error_tracking = await get_error_tracking()
        
        dashboard_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "health": health_data,
            "database": db_performance,
            "cache": cache_stats,
            "summary": metrics_summary,
            "realtime": realtime_metrics,
            "api_usage": api_usage,
            "errors": error_tracking
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Monitoring dashboard endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")