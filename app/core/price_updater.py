"""
Real-time price update system for Quick Commerce Deals platform.
This module implements task 3.2 requirements:
- Background task system for simulating price updates every few seconds
- Concurrent price updates across multiple platforms without conflicts
- Logging and monitoring for price update operations
"""

import asyncio
import logging
import random
import threading
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_, func
from app.db.database import engine
from app.models.platform import Platform
from app.models.product import Product
from app.models.pricing import CurrentPrice, PriceHistory

logger = logging.getLogger(__name__)


@dataclass
class UpdateMetrics:
    """Metrics for price update operations."""
    total_updates: int = 0
    successful_updates: int = 0
    failed_updates: int = 0
    price_increases: int = 0
    price_decreases: int = 0
    new_discounts: int = 0
    surge_pricing_events: int = 0
    conflicts_resolved: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    last_update_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_updates == 0:
            return 0.0
        return (self.successful_updates / self.total_updates) * 100
    
    @property
    def runtime(self) -> timedelta:
        """Calculate total runtime."""
        return datetime.now() - self.start_time
    
    @property
    def updates_per_minute(self) -> float:
        """Calculate updates per minute."""
        runtime_minutes = self.runtime.total_seconds() / 60
        if runtime_minutes == 0:
            return 0.0
        return self.total_updates / runtime_minutes


@dataclass
class PriceUpdateConfig:
    """Configuration for price update system."""
    update_interval_seconds: int = 5
    batch_size: int = 50
    max_price_change_percent: float = 15.0
    discount_probability: float = 0.15
    surge_probability: float = 0.05
    max_workers: int = 5
    enable_monitoring: bool = True
    log_level: str = "INFO"
    
    # Category-specific volatility settings
    category_volatility: Dict[str, float] = field(default_factory=lambda: {
        "fruits": 0.8,
        "vegetables": 0.8,
        "dairy": 0.3,
        "snacks": 0.2,
        "staples": 0.1
    })
    
    # Time-based pricing adjustments
    time_adjustments: Dict[str, float] = field(default_factory=lambda: {
        "morning_rush": 0.02,    # 7-9 AM
        "evening_rush": 0.02,    # 6-8 PM
        "late_night": -0.01      # 11 PM - 6 AM
    })


class PriceUpdateEngine:
    """
    Core engine for real-time price updates with conflict resolution.
    """
    
    def __init__(self, config: PriceUpdateConfig):
        self.config = config
        self.session_factory = sessionmaker(bind=engine)
        self.metrics = UpdateMetrics()
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
        self.is_running = False
        self.shutdown_event = threading.Event()
        
        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.PriceUpdateEngine")
        self.logger.setLevel(getattr(logging, config.log_level))
    
    def calculate_price_change(self, current_price: CurrentPrice, product: Product) -> Dict:
        """
        Calculate new price based on market simulation and time factors.
        """
        # Get category-specific volatility
        volatility = self._get_category_volatility(product.name)
        
        # Base price change calculation
        max_change = self.config.max_price_change_percent * volatility / 100
        price_change_percent = random.uniform(-max_change, max_change)
        
        # Apply time-based adjustments
        price_change_percent += self._get_time_adjustment()
        
        # Calculate new price
        old_price = current_price.price
        new_price = old_price * (1 + Decimal(str(price_change_percent)))
        new_price = new_price.quantize(Decimal('0.01'))
        
        # Ensure minimum price
        min_price = Decimal('5.00')
        if new_price < min_price:
            new_price = min_price
        
        # Determine change type and amount
        if new_price > old_price:
            change_type = "increase"
            change_amount = new_price - old_price
        elif new_price < old_price:
            change_type = "decrease"
            change_amount = old_price - new_price
        else:
            change_type = "no_change"
            change_amount = Decimal('0.00')
        
        # Handle discount and surge pricing
        discount_info = self._calculate_discount_surge(new_price)
        
        return {
            "new_price": discount_info["final_price"],
            "original_price": discount_info["original_price"],
            "discount_percentage": discount_info["discount_percentage"],
            "is_surge": discount_info["is_surge"],
            "change_type": change_type,
            "change_amount": change_amount,
            "change_percentage": abs(price_change_percent * 100)
        }
    
    def _get_category_volatility(self, product_name: str) -> float:
        """Get price volatility based on product category."""
        product_name_lower = product_name.lower()
        
        for category, volatility in self.config.category_volatility.items():
            if category in product_name_lower:
                return volatility
        
        return 0.3  # Default volatility
    
    def _get_time_adjustment(self) -> float:
        """Get time-based price adjustment."""
        hour = datetime.now().hour
        
        # Morning rush (7-9 AM)
        if 7 <= hour <= 9:
            return random.uniform(0, self.config.time_adjustments["morning_rush"])
        
        # Evening rush (6-8 PM)
        elif 18 <= hour <= 20:
            return random.uniform(0, self.config.time_adjustments["evening_rush"])
        
        # Late night (11 PM - 6 AM)
        elif hour >= 23 or hour <= 6:
            return random.uniform(self.config.time_adjustments["late_night"], 0)
        
        return 0.0
    
    def _calculate_discount_surge(self, base_price: Decimal) -> Dict:
        """Calculate discount or surge pricing scenarios."""
        # Random discount application
        if random.random() < self.config.discount_probability:
            discount_percentage = random.randint(5, 30)
            final_price = base_price * (1 - Decimal(discount_percentage) / 100)
            final_price = final_price.quantize(Decimal('0.01'))
            
            return {
                "final_price": final_price,
                "original_price": base_price,
                "discount_percentage": discount_percentage,
                "is_surge": False
            }
        
        # Surge pricing scenario
        elif random.random() < self.config.surge_probability:
            surge_multiplier = random.uniform(1.2, 1.8)
            final_price = base_price * Decimal(str(surge_multiplier))
            final_price = final_price.quantize(Decimal('0.01'))
            
            return {
                "final_price": final_price,
                "original_price": base_price,
                "discount_percentage": None,
                "is_surge": True
            }
        
        # No special pricing
        return {
            "final_price": base_price,
            "original_price": None,
            "discount_percentage": None,
            "is_surge": False
        }
    
    def update_single_price(self, current_price: CurrentPrice, product: Product) -> bool:
        """
        Update a single product price with conflict resolution.
        """
        session = self.session_factory()
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Re-fetch with row-level locking to prevent conflicts
                fresh_price = session.query(CurrentPrice).filter(
                    and_(
                        CurrentPrice.product_id == current_price.product_id,
                        CurrentPrice.platform_id == current_price.platform_id
                    )
                ).with_for_update().first()
                
                if not fresh_price:
                    self.logger.warning(f"Price entry not found for product {product.name}")
                    return False
                
                # Calculate new price
                price_update = self.calculate_price_change(fresh_price, product)
                
                # Store old values for history
                old_price = fresh_price.price
                old_discount = fresh_price.discount_percentage
                
                # Update current price
                fresh_price.price = price_update["new_price"]
                fresh_price.original_price = price_update["original_price"]
                fresh_price.discount_percentage = price_update["discount_percentage"]
                fresh_price.last_updated = datetime.now()
                
                # Randomly update availability (simulate stock changes)
                if random.random() < 0.05:  # 5% chance
                    fresh_price.is_available = not fresh_price.is_available
                    fresh_price.stock_status = random.choice(['in_stock', 'low_stock', 'out_of_stock'])
                
                # Create price history entry
                price_history = PriceHistory(
                    product_id=product.id,
                    platform_id=fresh_price.platform_id,
                    price=price_update["new_price"],
                    original_price=price_update["original_price"],
                    discount_percentage=price_update["discount_percentage"],
                    price_change_type=price_update["change_type"],
                    price_change_amount=price_update["change_amount"],
                    price_change_percentage=price_update["change_percentage"],
                    stock_status=fresh_price.stock_status,
                    source="price_update_engine"
                )
                
                session.add(price_history)
                session.commit()
                
                # Update metrics
                self._update_metrics(price_update, retry_count > 0)
                
                self.logger.debug(f"Updated {product.name} on platform {fresh_price.platform_id}: "
                                f"₹{old_price} → ₹{price_update['new_price']} ({price_update['change_type']})")
                
                return True
                
            except Exception as e:
                session.rollback()
                retry_count += 1
                
                if retry_count < max_retries:
                    self.logger.warning(f"Retry {retry_count} for {product.name}: {str(e)}")
                    time.sleep(0.1 * retry_count)  # Exponential backoff
                else:
                    self.logger.error(f"Failed to update {product.name} after {max_retries} retries: {str(e)}")
                    self.metrics.failed_updates += 1
                    return False
            
            finally:
                session.close()
        
        return False
    
    def _update_metrics(self, price_update: Dict, was_conflict: bool):
        """Update internal metrics."""
        self.metrics.successful_updates += 1
        self.metrics.last_update_time = datetime.now()
        
        if was_conflict:
            self.metrics.conflicts_resolved += 1
        
        if price_update["change_type"] == "increase":
            self.metrics.price_increases += 1
        elif price_update["change_type"] == "decrease":
            self.metrics.price_decreases += 1
        
        if price_update["discount_percentage"]:
            self.metrics.new_discounts += 1
        
        if price_update["is_surge"]:
            self.metrics.surge_pricing_events += 1
    
    def get_update_batch(self) -> List[tuple]:
        """Get a batch of products for price updates."""
        session = self.session_factory()
        
        try:
            # Get random products with their current prices
            query = session.query(CurrentPrice, Product).join(Product).filter(
                and_(
                    CurrentPrice.is_available == True,
                    Product.is_active == True
                )
            ).order_by(func.random()).limit(self.config.batch_size)
            
            return query.all()
            
        finally:
            session.close()
    
    def process_batch(self, batch: List[tuple]) -> int:
        """Process a batch of price updates concurrently."""
        if not batch:
            return 0
        
        # Submit all updates to thread pool
        futures = []
        for current_price, product in batch:
            future = self.executor.submit(self.update_single_price, current_price, product)
            futures.append(future)
        
        # Wait for completion and count successes
        successful_updates = 0
        for future in futures:
            try:
                if future.result(timeout=10):  # 10 second timeout
                    successful_updates += 1
            except Exception as e:
                self.logger.error(f"Batch update error: {str(e)}")
                self.metrics.failed_updates += 1
        
        self.metrics.total_updates += len(batch)
        return successful_updates
    
    def run_update_cycle(self):
        """Run a single update cycle."""
        try:
            # Get batch of products to update
            batch = self.get_update_batch()
            
            if not batch:
                self.logger.warning("No products available for update")
                return 0
            
            self.logger.debug(f"Processing batch of {len(batch)} products")
            
            # Process batch concurrently
            successful_updates = self.process_batch(batch)
            
            self.logger.info(f"Update cycle completed: {successful_updates}/{len(batch)} successful")
            return successful_updates
            
        except Exception as e:
            self.logger.error(f"Error in update cycle: {str(e)}")
            return 0
    
    def start_continuous_updates(self, on_cycle_complete: Optional[Callable] = None):
        """Start continuous price updates."""
        self.is_running = True
        self.logger.info("🚀 Starting continuous price updates")
        self.logger.info(f"   Update interval: {self.config.update_interval_seconds}s")
        self.logger.info(f"   Batch size: {self.config.batch_size}")
        self.logger.info(f"   Max workers: {self.config.max_workers}")
        
        cycle_count = 0
        
        try:
            while self.is_running and not self.shutdown_event.is_set():
                cycle_count += 1
                
                # Run update cycle
                successful_updates = self.run_update_cycle()
                
                # Call callback if provided
                if on_cycle_complete:
                    on_cycle_complete(cycle_count, successful_updates, self.metrics)
                
                # Log metrics periodically
                if cycle_count % 10 == 0:
                    self.log_metrics()
                
                # Wait for next cycle
                if self.shutdown_event.wait(self.config.update_interval_seconds):
                    break  # Shutdown requested
                    
        except KeyboardInterrupt:
            self.logger.info("Shutdown signal received")
        except Exception as e:
            self.logger.error(f"Error in continuous update loop: {str(e)}")
        finally:
            self.is_running = False
            self.logger.info("🛑 Price update engine stopped")
            self.log_metrics()
    
    def stop(self):
        """Stop the price update engine."""
        self.logger.info("Stopping price update engine...")
        self.is_running = False
        self.shutdown_event.set()
    
    def log_metrics(self):
        """Log current metrics."""
        self.logger.info("📊 Price Update Metrics:")
        self.logger.info(f"   Runtime: {self.metrics.runtime}")
        self.logger.info(f"   Total Updates: {self.metrics.total_updates}")
        self.logger.info(f"   Success Rate: {self.metrics.success_rate:.1f}%")
        self.logger.info(f"   Updates/min: {self.metrics.updates_per_minute:.1f}")
        self.logger.info(f"   Price Changes: ↑{self.metrics.price_increases} ↓{self.metrics.price_decreases}")
        self.logger.info(f"   New Discounts: {self.metrics.new_discounts}")
        self.logger.info(f"   Surge Events: {self.metrics.surge_pricing_events}")
        self.logger.info(f"   Conflicts Resolved: {self.metrics.conflicts_resolved}")
    
    def get_metrics(self) -> UpdateMetrics:
        """Get current metrics."""
        return self.metrics
    
    def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up price update engine...")
        self.executor.shutdown(wait=True)


class PriceUpdateManager:
    """
    Manager class for the price update system with monitoring capabilities.
    """
    
    def __init__(self, config: Optional[PriceUpdateConfig] = None):
        self.config = config or PriceUpdateConfig()
        self.engine = PriceUpdateEngine(self.config)
        self.monitoring_enabled = self.config.enable_monitoring
        self.logger = logging.getLogger(f"{__name__}.PriceUpdateManager")
    
    def start(self, blocking: bool = True):
        """Start the price update system."""
        def on_cycle_complete(cycle: int, successful: int, metrics: UpdateMetrics):
            if self.monitoring_enabled and cycle % 5 == 0:
                self.logger.info(f"Cycle #{cycle}: {successful} updates, "
                               f"{metrics.success_rate:.1f}% success rate")
        
        if blocking:
            self.engine.start_continuous_updates(on_cycle_complete)
        else:
            # Start in background thread
            update_thread = threading.Thread(
                target=self.engine.start_continuous_updates,
                args=(on_cycle_complete,),
                daemon=True
            )
            update_thread.start()
            return update_thread
    
    def stop(self):
        """Stop the price update system."""
        self.engine.stop()
    
    def get_status(self) -> Dict:
        """Get current system status."""
        metrics = self.engine.get_metrics()
        
        return {
            "is_running": self.engine.is_running,
            "runtime": str(metrics.runtime),
            "total_updates": metrics.total_updates,
            "success_rate": metrics.success_rate,
            "updates_per_minute": metrics.updates_per_minute,
            "last_update": metrics.last_update_time.isoformat() if metrics.last_update_time else None,
            "config": {
                "update_interval": self.config.update_interval_seconds,
                "batch_size": self.config.batch_size,
                "max_workers": self.config.max_workers
            }
        }
    
    def cleanup(self):
        """Cleanup resources."""
        self.engine.cleanup()