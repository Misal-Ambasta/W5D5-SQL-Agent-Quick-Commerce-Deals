"""
Application startup and monitoring initialization
"""
import asyncio
from app.core.logging import logger
from app.core.monitoring import system_monitor


async def initialize_monitoring():
    """Initialize all monitoring systems"""
    try:
        # Start system monitoring
        await system_monitor.start_monitoring(interval_seconds=60)
        logger.info("System monitoring initialized successfully")
        
        # Log startup metrics
        logger.info("Monitoring systems started", extra={
            "event_type": "monitoring_startup",
            "systems": ["database_monitor", "cache_monitor", "system_monitor", "alert_manager"]
        })
        
    except Exception as e:
        logger.warning(f"Some monitoring systems failed to initialize: {e}")
        # Don't raise in development mode - allow API to start without full monitoring


async def shutdown_monitoring():
    """Shutdown monitoring systems gracefully"""
    try:
        await system_monitor.stop_monitoring()
        logger.info("Monitoring systems shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during monitoring shutdown: {e}")