"""
Monitoring endpoints for database and cache performance metrics
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.core.database import db_monitor, db_health_checker
from app.core.cache import cache_manager

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def get_system_health():
    """
    Get comprehensive system health status including database and cache
    """
    try:
        # Get database health
        db_health = await db_health_checker.check_database_health()
        
        # Get cache health
        cache_health = await cache_manager.health_check()
        
        # Determine overall system health
        overall_status = "healthy"
        if db_health["status"] != "healthy" or cache_health["overall_status"] != "healthy":
            if db_health["status"] == "unhealthy" or cache_health["overall_status"] == "unhealthy":
                overall_status = "unhealthy"
            else:
                overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": db_health.get("timestamp", "unknown"),
            "components": {
                "database": {
                    "status": db_health["status"],
                    "connection_pool": db_health.get("connection_pool", {}),
                    "recent_errors": len(db_health.get("recent_errors", [])),
                    "recommendations": db_health.get("recommendations", [])
                },
                "cache": {
                    "status": cache_health["overall_status"],
                    "memory_cache": cache_health["memory_cache"]["status"],
                    "redis_cache": cache_health["redis_cache"]["status"]
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/database/performance", response_model=Dict[str, Any])
async def get_database_performance():
    """
    Get detailed database performance metrics
    """
    try:
        performance_summary = db_monitor.get_performance_summary()
        return {
            "performance_metrics": performance_summary,
            "connection_pool": db_health_checker.get_connection_pool_stats(),
            "optimization_suggestions": db_monitor.get_query_optimization_suggestions()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database performance: {str(e)}")


@router.get("/database/slow-queries", response_model=Dict[str, Any])
async def get_slow_queries(limit: int = 20):
    """
    Get recent slow queries for performance analysis
    """
    try:
        if limit > 100:
            limit = 100  # Cap the limit to prevent excessive data
        
        slow_queries = db_monitor.get_slow_queries(limit=limit)
        
        return {
            "slow_queries": slow_queries,
            "total_count": len(slow_queries),
            "threshold_seconds": db_monitor.slow_query_threshold
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get slow queries: {str(e)}")


@router.get("/cache/stats", response_model=Dict[str, Any])
async def get_cache_statistics():
    """
    Get comprehensive cache statistics and performance metrics
    """
    try:
        cache_stats = cache_manager.get_cache_stats()
        return {
            "cache_statistics": cache_stats,
            "health_status": await cache_manager.health_check()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache statistics: {str(e)}")


@router.post("/cache/invalidate/{namespace}")
async def invalidate_cache_namespace(namespace: str):
    """
    Invalidate all cache entries in a specific namespace
    """
    try:
        invalidated_count = await cache_manager.invalidate_namespace(namespace)
        
        return {
            "message": f"Successfully invalidated cache namespace: {namespace}",
            "invalidated_entries": invalidated_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache namespace: {str(e)}")


@router.post("/cache/invalidate/tags")
async def invalidate_cache_by_tags(tags: list[str]):
    """
    Invalidate cache entries by tags
    """
    try:
        if not tags:
            raise HTTPException(status_code=400, detail="At least one tag must be provided")
        
        invalidated_count = await cache_manager.invalidate_by_tags(tags)
        
        return {
            "message": f"Successfully invalidated cache entries with tags: {', '.join(tags)}",
            "invalidated_entries": invalidated_count,
            "tags": tags
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache by tags: {str(e)}")


@router.get("/metrics/summary", response_model=Dict[str, Any])
async def get_metrics_summary():
    """
    Get a comprehensive summary of all system metrics
    """
    try:
        # Get database metrics
        db_performance = db_monitor.get_performance_summary()
        db_pool_stats = db_health_checker.get_connection_pool_stats()
        
        # Get cache metrics
        cache_stats = cache_manager.get_cache_stats()
        
        # Calculate some derived metrics
        total_requests = db_performance["overall_stats"]["total_queries"]
        cache_hit_ratio = cache_stats["performance"]["hit_ratio"]
        
        # System efficiency score (simple calculation)
        efficiency_score = 0
        if total_requests > 0:
            error_rate = db_performance["overall_stats"]["error_rate"]
            avg_response_time = db_performance["overall_stats"]["avg_execution_time"]
            
            # Score based on error rate (lower is better)
            error_score = max(0, 100 - (error_rate * 1000))  # Penalize errors heavily
            
            # Score based on response time (lower is better, cap at 1 second)
            response_score = max(0, 100 - (min(avg_response_time, 1.0) * 100))
            
            # Score based on cache hit ratio (higher is better)
            cache_score = cache_hit_ratio * 100
            
            efficiency_score = (error_score + response_score + cache_score) / 3
        
        return {
            "summary": {
                "total_database_queries": total_requests,
                "database_error_rate": db_performance["overall_stats"]["error_rate"],
                "average_query_time": db_performance["overall_stats"]["avg_execution_time"],
                "cache_hit_ratio": cache_hit_ratio,
                "connection_pool_utilization": db_pool_stats.get("utilization_percent", 0) / 100,
                "system_efficiency_score": round(efficiency_score, 2)
            },
            "database": {
                "performance": db_performance["overall_stats"],
                "connection_pool": db_pool_stats,
                "recent_performance": db_performance["recent_performance"]
            },
            "cache": {
                "performance": cache_stats["performance"],
                "memory_cache": cache_stats["memory_cache"],
                "redis_connected": cache_stats["redis_connected"]
            },
            "recommendations": {
                "database": db_monitor.get_query_optimization_suggestions()[:5],
                "general": []
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics summary: {str(e)}")


@router.get("/metrics/realtime", response_model=Dict[str, Any])
async def get_realtime_metrics():
    """
    Get real-time system metrics for monitoring dashboards
    """
    try:
        from datetime import datetime, timedelta
        
        current_time = datetime.now()
        
        # Get recent metrics (last 5 minutes)
        recent_queries = [
            q for q in db_monitor.query_history 
            if (current_time - q.timestamp) <= timedelta(minutes=5)
        ]
        
        # Calculate real-time stats
        recent_successful = [q for q in recent_queries if q.success]
        recent_errors = [q for q in recent_queries if not q.success]
        
        # Get current connection pool status
        pool_stats = db_health_checker.get_connection_pool_stats()
        
        # Get cache performance
        cache_stats = cache_manager.get_cache_stats()
        
        return {
            "timestamp": current_time.isoformat(),
            "interval_minutes": 5,
            "database": {
                "queries_per_minute": len(recent_queries) / 5,
                "errors_per_minute": len(recent_errors) / 5,
                "avg_response_time": (
                    sum(q.execution_time for q in recent_successful) / len(recent_successful)
                    if recent_successful else 0
                ),
                "active_connections": pool_stats.get("checked_out", 0),
                "available_connections": pool_stats.get("available_connections", 0)
            },
            "cache": {
                "hit_ratio": cache_stats["performance"]["hit_ratio"],
                "total_hits": cache_stats["performance"]["cache_hits"],
                "total_misses": cache_stats["performance"]["cache_misses"],
                "memory_cache_entries": cache_stats["memory_cache"]["total_entries"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get real-time metrics: {str(e)}")