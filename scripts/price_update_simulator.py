#!/usr/bin/env python3
"""
Real-time price update simulation script for Quick Commerce Deals platform.
This script implements task 3.2 requirements:
- Create background task system for simulating price updates every few seconds
- Implement concurrent price updates across multiple platforms without conflicts
- Add logging and monitoring for price update operations

Enhanced with comprehensive monitoring and conflict resolution.
"""

import sys
import os
import random
import logging
import signal
import argparse
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
import threading
import time

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.price_updater import PriceUpdateManager, PriceUpdateConfig
from app.core.monitoring import get_monitor, PriceUpdateEvent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_flag = threading.Event()


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_flag.set()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Real-time price update simulator")
    parser.add_argument("--interval", type=int, default=5, 
                       help="Update interval in seconds (default: 5)")
    parser.add_argument("--batch-size", type=int, default=50,
                       help="Batch size for updates (default: 50)")
    parser.add_argument("--max-workers", type=int, default=5,
                       help="Maximum worker threads (default: 5)")
    parser.add_argument("--log-level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help="Log level (default: INFO)")
    parser.add_argument("--monitoring", action='store_true', default=True,
                       help="Enable monitoring (default: True)")
    parser.add_argument("--export-report", type=str,
                       help="Export monitoring report to file")
    parser.add_argument("--duration", type=int,
                       help="Run for specified duration in minutes")
    
    return parser.parse_args()


def create_config_from_args(args) -> PriceUpdateConfig:
    """Create configuration from command line arguments."""
    return PriceUpdateConfig(
        update_interval_seconds=args.interval,
        batch_size=args.batch_size,
        max_workers=args.max_workers,
        enable_monitoring=args.monitoring,
        log_level=args.log_level
    )


def main():
    """Enhanced main function with monitoring and configuration options."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Configure logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    manager = None
    monitor = get_monitor()
    
    try:
        logger.info("🎯 Enhanced Quick Commerce Price Update Simulator")
        logger.info("=" * 60)
        logger.info(f"Configuration:")
        logger.info(f"  Update interval: {args.interval} seconds")
        logger.info(f"  Batch size: {args.batch_size}")
        logger.info(f"  Max workers: {args.max_workers}")
        logger.info(f"  Monitoring: {'Enabled' if args.monitoring else 'Disabled'}")
        logger.info(f"  Log level: {args.log_level}")
        
        if args.duration:
            logger.info(f"  Duration: {args.duration} minutes")
        
        # Create configuration and manager
        config = create_config_from_args(args)
        manager = PriceUpdateManager(config)
        
        # Start monitoring if enabled
        if args.monitoring:
            logger.info("📊 Monitoring enabled - tracking all price updates")
        
        # Start price updates
        if args.duration:
            # Run for specified duration
            logger.info(f"🕐 Running for {args.duration} minutes...")
            
            # Start in background
            update_thread = manager.start(blocking=False)
            
            # Wait for duration or shutdown signal
            end_time = time.time() + (args.duration * 60)
            while time.time() < end_time and not shutdown_flag.is_set():
                time.sleep(1)
            
            # Stop the manager
            manager.stop()
            update_thread.join(timeout=10)
            
        else:
            # Run continuously until interrupted
            logger.info("🔄 Running continuously - Press Ctrl+C to stop")
            manager.start(blocking=True)
        
        # Export monitoring report if requested
        if args.export_report and args.monitoring:
            logger.info(f"📄 Exporting monitoring report to {args.export_report}")
            report = monitor.generate_report(hours=24)
            
            with open(args.export_report, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"✅ Report exported successfully")
        
        # Print final statistics
        if args.monitoring:
            logger.info("\n📊 Final Statistics:")
            health = monitor.get_system_health()
            logger.info(f"  Total products monitored: {health.total_products}")
            logger.info(f"  Active platforms: {health.active_platforms}")
            logger.info(f"  Successful updates (last hour): {health.successful_updates_last_hour}")
            logger.info(f"  Failed updates (last hour): {health.failed_updates_last_hour}")
            logger.info(f"  Average processing time: {health.average_processing_time_ms:.2f}ms")
            logger.info(f"  Price volatility index: {health.price_volatility_index:.2f}")
        
        logger.info("✅ Price update simulation completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in price update simulator: {str(e)}")
        return False
        
    finally:
        if manager:
            manager.cleanup()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)