#!/usr/bin/env python3
"""
Test script for data simulation and seeding functionality.
This script validates task 3.1 and 3.2 implementations.
"""

import sys
import os
import logging
import time
from datetime import datetime, timedelta
from decimal import Decimal

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, and_
from app.db.database import engine
from app.models.platform import Platform
from app.models.product import Product, ProductCategory, ProductBrand
from app.models.pricing import CurrentPrice, PriceHistory, Discount, PromotionalCampaign
from app.models.inventory import InventoryLevel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataSimulationTester:
    """
    Tests the data simulation and seeding functionality.
    """
    
    def __init__(self):
        self.session = sessionmaker(bind=engine)()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    def test_basic_data_integrity(self) -> bool:
        """Test basic data integrity and relationships."""
        logger.info("Testing basic data integrity...")
        
        try:
            # Test platform data
            platforms = self.session.query(Platform).all()
            if len(platforms) < 4:
                logger.error(f"Expected at least 4 platforms, found {len(platforms)}")
                return False
            
            # Test product data
            products = self.session.query(Product).all()
            if len(products) < 50:
                logger.error(f"Expected at least 50 products, found {len(products)}")
                return False
            
            # Test categories and brands
            categories = self.session.query(ProductCategory).all()
            brands = self.session.query(ProductBrand).all()
            
            logger.info(f"✅ Found {len(platforms)} platforms, {len(products)} products, "
                       f"{len(categories)} categories, {len(brands)} brands")
            
            # Test product relationships
            products_with_categories = self.session.query(Product).filter(
                Product.category_id.isnot(None)
            ).count()
            
            if products_with_categories < len(products) * 0.8:
                logger.error("Less than 80% of products have categories assigned")
                return False
            
            logger.info(f"✅ {products_with_categories}/{len(products)} products have categories")
            return True
            
        except Exception as e:
            logger.error(f"Error testing basic data integrity: {str(e)}")
            return False
    
    def test_pricing_data_quality(self) -> bool:
        """Test pricing data quality and variations."""
        logger.info("Testing pricing data quality...")
        
        try:
            # Test current prices
            current_prices = self.session.query(CurrentPrice).all()
            if len(current_prices) < 200:
                logger.error(f"Expected at least 200 price entries, found {len(current_prices)}")
                return False
            
            # Test platform pricing variations
            platform_price_stats = {}
            
            for platform in self.session.query(Platform).all():
                prices = self.session.query(CurrentPrice).filter(
                    CurrentPrice.platform_id == platform.id
                ).all()
                
                if not prices:
                    logger.error(f"No prices found for platform {platform.name}")
                    return False
                
                avg_price = sum(float(p.price) for p in prices) / len(prices)
                min_price = min(float(p.price) for p in prices)
                max_price = max(float(p.price) for p in prices)
                
                platform_price_stats[platform.name] = {
                    "count": len(prices),
                    "avg_price": avg_price,
                    "min_price": min_price,
                    "max_price": max_price
                }
            
            # Verify pricing variations between platforms
            avg_prices = [stats["avg_price"] for stats in platform_price_stats.values()]
            price_variation = (max(avg_prices) - min(avg_prices)) / min(avg_prices)
            
            if price_variation < 0.1:  # At least 10% variation expected
                logger.warning(f"Low price variation between platforms: {price_variation:.2%}")
            
            logger.info("✅ Platform pricing statistics:")
            for platform, stats in platform_price_stats.items():
                logger.info(f"   {platform}: {stats['count']} prices, "
                           f"avg ₹{stats['avg_price']:.2f}, "
                           f"range ₹{stats['min_price']:.2f}-₹{stats['max_price']:.2f}")
            
            # Test discount distribution
            discounted_prices = self.session.query(CurrentPrice).filter(
                CurrentPrice.discount_percentage.isnot(None)
            ).count()
            
            discount_rate = discounted_prices / len(current_prices)
            logger.info(f"✅ Discount rate: {discount_rate:.1%} ({discounted_prices}/{len(current_prices)})")
            
            if discount_rate < 0.1 or discount_rate > 0.5:
                logger.warning(f"Unusual discount rate: {discount_rate:.1%}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error testing pricing data quality: {str(e)}")
            return False
    
    def test_discount_and_promotional_data(self) -> bool:
        """Test discount and promotional campaign data."""
        logger.info("Testing discount and promotional data...")
        
        try:
            # Test discounts
            discounts = self.session.query(Discount).all()
            active_discounts = self.session.query(Discount).filter(
                and_(
                    Discount.is_active == True,
                    Discount.start_date <= datetime.now(),
                    Discount.end_date >= datetime.now()
                )
            ).all()
            
            logger.info(f"✅ Found {len(discounts)} total discounts, {len(active_discounts)} currently active")
            
            # Test discount types
            percentage_discounts = self.session.query(Discount).filter(
                Discount.discount_type == 'percentage'
            ).count()
            
            fixed_discounts = self.session.query(Discount).filter(
                Discount.discount_type == 'fixed_amount'
            ).count()
            
            logger.info(f"✅ Discount types: {percentage_discounts} percentage, {fixed_discounts} fixed amount")
            
            # Test promotional campaigns
            campaigns = self.session.query(PromotionalCampaign).all()
            active_campaigns = self.session.query(PromotionalCampaign).filter(
                and_(
                    PromotionalCampaign.is_active == True,
                    PromotionalCampaign.start_date <= datetime.now(),
                    PromotionalCampaign.end_date >= datetime.now()
                )
            ).all()
            
            logger.info(f"✅ Found {len(campaigns)} total campaigns, {len(active_campaigns)} currently active")
            
            # Test campaign types
            campaign_types = self.session.query(
                PromotionalCampaign.campaign_type,
                func.count(PromotionalCampaign.id)
            ).group_by(PromotionalCampaign.campaign_type).all()
            
            logger.info("✅ Campaign types:")
            for campaign_type, count in campaign_types:
                logger.info(f"   {campaign_type}: {count}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error testing discount and promotional data: {str(e)}")
            return False
    
    def test_inventory_data(self) -> bool:
        """Test inventory data completeness."""
        logger.info("Testing inventory data...")
        
        try:
            inventory_levels = self.session.query(InventoryLevel).all()
            
            # Check if we have inventory for all product-platform combinations
            products_count = self.session.query(Product).count()
            platforms_count = self.session.query(Platform).count()
            expected_inventory_entries = products_count * platforms_count
            
            if len(inventory_levels) < expected_inventory_entries * 0.8:
                logger.warning(f"Low inventory coverage: {len(inventory_levels)}/{expected_inventory_entries}")
            
            # Test stock level distribution
            stock_stats = self.session.query(
                func.min(InventoryLevel.stock_level),
                func.max(InventoryLevel.stock_level),
                func.avg(InventoryLevel.stock_level)
            ).first()
            
            logger.info(f"✅ Inventory levels: {len(inventory_levels)} entries")
            logger.info(f"   Stock range: {stock_stats[0]}-{stock_stats[1]}, avg: {stock_stats[2]:.1f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error testing inventory data: {str(e)}")
            return False
    
    def test_price_comparison_queries(self) -> bool:
        """Test sample price comparison queries."""
        logger.info("Testing price comparison queries...")
        
        try:
            # Test 1: Find cheapest onions across platforms
            onion_products = self.session.query(Product).filter(
                Product.name.ilike('%onion%')
            ).all()
            
            if onion_products:
                onion_prices = self.session.query(
                    CurrentPrice, Platform, Product
                ).join(Platform).join(Product).filter(
                    and_(
                        Product.name.ilike('%onion%'),
                        CurrentPrice.is_available == True
                    )
                ).order_by(CurrentPrice.price).all()
                
                if onion_prices:
                    cheapest = onion_prices[0]
                    logger.info(f"✅ Cheapest onions: {cheapest.Product.name} on {cheapest.Platform.display_name} "
                               f"for ₹{cheapest.CurrentPrice.price}")
                else:
                    logger.warning("No available onion prices found")
            
            # Test 2: Find products with 30%+ discount
            high_discount_products = self.session.query(
                CurrentPrice, Product, Platform
            ).join(Product).join(Platform).filter(
                and_(
                    CurrentPrice.discount_percentage >= 30,
                    CurrentPrice.is_available == True
                )
            ).limit(5).all()
            
            logger.info(f"✅ Found {len(high_discount_products)} products with 30%+ discount")
            for price, product, platform in high_discount_products:
                logger.info(f"   {product.name} on {platform.display_name}: "
                           f"{price.discount_percentage}% off (₹{price.price})")
            
            # Test 3: Compare fruit prices between platforms
            fruit_category = self.session.query(ProductCategory).filter(
                ProductCategory.name.ilike('%fruit%')
            ).first()
            
            if fruit_category:
                fruit_price_comparison = self.session.query(
                    Product.name,
                    Platform.display_name,
                    CurrentPrice.price
                ).join(CurrentPrice).join(Platform).filter(
                    and_(
                        Product.category_id == fruit_category.id,
                        CurrentPrice.is_available == True
                    )
                ).order_by(Product.name, CurrentPrice.price).limit(10).all()
                
                logger.info(f"✅ Sample fruit price comparison ({len(fruit_price_comparison)} entries):")
                for product_name, platform_name, price in fruit_price_comparison[:3]:
                    logger.info(f"   {product_name} on {platform_name}: ₹{price}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error testing price comparison queries: {str(e)}")
            return False
    
    def test_time_based_variations(self) -> bool:
        """Test time-based variations in discounts and campaigns."""
        logger.info("Testing time-based variations...")
        
        try:
            now = datetime.now()
            
            # Test campaigns with different time ranges
            future_campaigns = self.session.query(PromotionalCampaign).filter(
                PromotionalCampaign.start_date > now
            ).count()
            
            past_campaigns = self.session.query(PromotionalCampaign).filter(
                PromotionalCampaign.end_date < now
            ).count()
            
            current_campaigns = self.session.query(PromotionalCampaign).filter(
                and_(
                    PromotionalCampaign.start_date <= now,
                    PromotionalCampaign.end_date >= now
                )
            ).count()
            
            logger.info(f"✅ Campaign timeline: {past_campaigns} past, {current_campaigns} current, {future_campaigns} future")
            
            # Test discount duration variations
            discount_durations = self.session.query(
                func.extract('epoch', Discount.end_date - Discount.start_date) / 86400
            ).filter(
                Discount.start_date.isnot(None),
                Discount.end_date.isnot(None)
            ).all()
            
            if discount_durations:
                durations = [d[0] for d in discount_durations if d[0] is not None]
                avg_duration = sum(durations) / len(durations)
                logger.info(f"✅ Average discount duration: {avg_duration:.1f} days")
            
            return True
            
        except Exception as e:
            logger.error(f"Error testing time-based variations: {str(e)}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all data simulation tests."""
        logger.info("🧪 Starting Data Simulation Tests")
        logger.info("=" * 50)
        
        tests = [
            ("Basic Data Integrity", self.test_basic_data_integrity),
            ("Pricing Data Quality", self.test_pricing_data_quality),
            ("Discount & Promotional Data", self.test_discount_and_promotional_data),
            ("Inventory Data", self.test_inventory_data),
            ("Price Comparison Queries", self.test_price_comparison_queries),
            ("Time-based Variations", self.test_time_based_variations),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n🔍 Running: {test_name}")
            try:
                if test_func():
                    logger.info(f"✅ PASSED: {test_name}")
                    passed_tests += 1
                else:
                    logger.error(f"❌ FAILED: {test_name}")
            except Exception as e:
                logger.error(f"❌ ERROR in {test_name}: {str(e)}")
        
        logger.info(f"\n📊 Test Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 All tests passed! Data simulation is working correctly.")
            return True
        else:
            logger.error(f"❌ {total_tests - passed_tests} tests failed.")
            return False


def main():
    """Main function to run data simulation tests."""
    try:
        with DataSimulationTester() as tester:
            return tester.run_all_tests()
    except Exception as e:
        logger.error(f"❌ Error running tests: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)