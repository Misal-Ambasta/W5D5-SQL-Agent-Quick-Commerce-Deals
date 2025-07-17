#!/usr/bin/env python3
"""
Dummy data generation script for Quick Commerce Deals platform.
This script implements task 3.1 requirements:
- Generate realistic product data for multiple platforms
- Create price simulation with realistic variations across Blinkit, Zepto, Instamart, BigBasket Now
- Generate discount and promotional data with time-based variations

Requirements addressed:
- 2.1: Multi-platform product data with proper relationships
- 2.2: Realistic pricing variations and discount structures
"""

import sys
import os
import random
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any
import json

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from app.db.database import engine
from app.models.platform import Platform
from app.models.product import Product, ProductCategory, ProductBrand
from app.models.pricing import CurrentPrice, Discount, PromotionalCampaign, CampaignProduct
from app.models.inventory import InventoryLevel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Product data templates for realistic generation
PRODUCT_TEMPLATES = {
    "fruits": [
        {"name": "Bananas", "unit": "dozen", "base_price": 40, "category": "Fresh Fruits"},
        {"name": "Apples", "unit": "kg", "base_price": 120, "category": "Fresh Fruits"},
        {"name": "Oranges", "unit": "kg", "base_price": 80, "category": "Fresh Fruits"},
        {"name": "Mangoes", "unit": "kg", "base_price": 150, "category": "Fresh Fruits"},
        {"name": "Grapes", "unit": "kg", "base_price": 100, "category": "Fresh Fruits"},
        {"name": "Pomegranate", "unit": "piece", "base_price": 60, "category": "Fresh Fruits"},
        {"name": "Watermelon", "unit": "piece", "base_price": 80, "category": "Fresh Fruits"},
        {"name": "Pineapple", "unit": "piece", "base_price": 50, "category": "Fresh Fruits"},
    ],
    "vegetables": [
        {"name": "Onions", "unit": "kg", "base_price": 30, "category": "Fresh Vegetables"},
        {"name": "Tomatoes", "unit": "kg", "base_price": 40, "category": "Fresh Vegetables"},
        {"name": "Potatoes", "unit": "kg", "base_price": 25, "category": "Fresh Vegetables"},
        {"name": "Carrots", "unit": "kg", "base_price": 35, "category": "Fresh Vegetables"},
        {"name": "Capsicum", "unit": "kg", "base_price": 60, "category": "Fresh Vegetables"},
        {"name": "Cauliflower", "unit": "piece", "base_price": 40, "category": "Fresh Vegetables"},
        {"name": "Cabbage", "unit": "piece", "base_price": 30, "category": "Fresh Vegetables"},
        {"name": "Spinach", "unit": "bunch", "base_price": 20, "category": "Fresh Vegetables"},
    ],
    "dairy": [
        {"name": "Milk", "unit": "1L", "base_price": 60, "category": "Dairy & Eggs", "brand": "Amul"},
        {"name": "Curd", "unit": "400g", "base_price": 35, "category": "Dairy & Eggs", "brand": "Amul"},
        {"name": "Paneer", "unit": "200g", "base_price": 80, "category": "Dairy & Eggs", "brand": "Amul"},
        {"name": "Butter", "unit": "100g", "base_price": 50, "category": "Dairy & Eggs", "brand": "Amul"},
        {"name": "Cheese", "unit": "200g", "base_price": 120, "category": "Dairy & Eggs", "brand": "Britannia"},
        {"name": "Eggs", "unit": "dozen", "base_price": 70, "category": "Dairy & Eggs"},
        {"name": "Yogurt", "unit": "400g", "base_price": 40, "category": "Dairy & Eggs", "brand": "Nestle"},
    ],
    "snacks": [
        {"name": "Biscuits", "unit": "pack", "base_price": 25, "category": "Snacks & Beverages", "brand": "Britannia"},
        {"name": "Chips", "unit": "pack", "base_price": 20, "category": "Snacks & Beverages"},
        {"name": "Namkeen", "unit": "pack", "base_price": 30, "category": "Snacks & Beverages"},
        {"name": "Chocolate", "unit": "pack", "base_price": 40, "category": "Snacks & Beverages", "brand": "Nestle"},
        {"name": "Cold Drink", "unit": "bottle", "base_price": 35, "category": "Snacks & Beverages"},
        {"name": "Juice", "unit": "1L", "base_price": 80, "category": "Snacks & Beverages"},
    ],
    "staples": [
        {"name": "Rice", "unit": "kg", "base_price": 50, "category": "Pantry Staples", "brand": "Tata"},
        {"name": "Wheat Flour", "unit": "kg", "base_price": 40, "category": "Pantry Staples"},
        {"name": "Sugar", "unit": "kg", "base_price": 45, "category": "Pantry Staples"},
        {"name": "Salt", "unit": "kg", "base_price": 20, "category": "Pantry Staples", "brand": "Tata"},
        {"name": "Cooking Oil", "unit": "1L", "base_price": 120, "category": "Pantry Staples"},
        {"name": "Dal", "unit": "kg", "base_price": 80, "category": "Pantry Staples", "brand": "Tata"},
    ]
}

# Platform-specific pricing variations (multipliers)
PLATFORM_PRICING_VARIATIONS = {
    "blinkit": {"min": 0.95, "max": 1.15, "avg_discount": 8},
    "zepto": {"min": 0.90, "max": 1.20, "avg_discount": 12},
    "instamart": {"min": 0.92, "max": 1.18, "avg_discount": 10},
    "bigbasket_now": {"min": 0.88, "max": 1.25, "avg_discount": 15},
    "dunzo": {"min": 0.93, "max": 1.22, "avg_discount": 9}
}

# Discount templates for realistic promotional data
DISCOUNT_TEMPLATES = [
    {"type": "percentage", "value": 10, "title": "10% Off on All Products", "min_order": 200},
    {"type": "percentage", "value": 15, "title": "15% Off on Orders Above ₹300", "min_order": 300},
    {"type": "percentage", "value": 20, "title": "20% Off on Orders Above ₹500", "min_order": 500},
    {"type": "percentage", "value": 25, "title": "25% Off on Orders Above ₹750", "min_order": 750},
    {"type": "percentage", "value": 30, "title": "30% Off on Orders Above ₹1000", "min_order": 1000},
    {"type": "fixed_amount", "value": 50, "title": "₹50 Off on Orders Above ₹300", "min_order": 300},
    {"type": "fixed_amount", "value": 100, "title": "₹100 Off on Orders Above ₹500", "min_order": 500},
    {"type": "fixed_amount", "value": 150, "title": "₹150 Off on Orders Above ₹750", "min_order": 750},
]

CAMPAIGN_TEMPLATES = [
    {"name": "Weekend Flash Sale", "type": "flash_sale", "duration_hours": 48},
    {"name": "Monday Madness", "type": "weekday_special", "duration_hours": 24},
    {"name": "Fresh Fruits Festival", "type": "category_sale", "duration_hours": 72},
    {"name": "Dairy Delight Deals", "type": "category_sale", "duration_hours": 72},
    {"name": "Midnight Munchies", "type": "time_based", "duration_hours": 6},
    {"name": "Early Bird Special", "type": "time_based", "duration_hours": 4},
    {"name": "Bulk Buy Bonanza", "type": "bulk_discount", "duration_hours": 168},
]


class DummyDataGenerator:
    """
    Generates realistic dummy data for the Quick Commerce Deals platform.
    """
    
    def __init__(self):
        self.session = sessionmaker(bind=engine)()
        self.platforms = []
        self.categories = []
        self.brands = []
        self.products = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()
    
    def load_existing_data(self):
        """Load existing platforms, categories, and brands from database."""
        self.platforms = self.session.query(Platform).all()
        self.categories = self.session.query(ProductCategory).all()
        self.brands = self.session.query(ProductBrand).all()
        
        logger.info(f"Loaded {len(self.platforms)} platforms, {len(self.categories)} categories, {len(self.brands)} brands")
    
    def generate_products(self, count_per_category: int = 10) -> List[Product]:
        """Generate realistic product data."""
        logger.info("Generating product data...")
        
        products = []
        product_id_counter = 1
        
        for category_name, product_list in PRODUCT_TEMPLATES.items():
            # Find the category
            category = next((cat for cat in self.categories if category_name.replace('_', ' ').title() in cat.name), None)
            if not category:
                logger.warning(f"Category not found for {category_name}, skipping")
                continue
            
            for template in product_list:
                for variant in range(count_per_category):
                    # Create product variations
                    product_name = template["name"]
                    if variant > 0:
                        # Add variations like "Premium", "Organic", "Fresh", etc.
                        variations = ["Premium", "Organic", "Fresh", "Select", "Special", "Local"]
                        product_name = f"{random.choice(variations)} {product_name}"
                    
                    # Find brand if specified
                    brand = None
                    if "brand" in template:
                        brand = next((b for b in self.brands if b.name == template["brand"]), None)
                    
                    # Create product
                    product = Product(
                        name=product_name,
                        slug=f"{product_name.lower().replace(' ', '-')}-{product_id_counter}",
                        category_id=category.id,
                        brand_id=brand.id if brand else None,
                        description=f"High quality {product_name.lower()} - {template['unit']}",
                        short_description=f"{product_name} - {template['unit']}",
                        barcode=f"QCD{product_id_counter:08d}",
                        pack_size=template["unit"],
                        weight=self._calculate_weight(template["unit"]),
                        weight_unit='g',
                        is_organic=random.choice([True, False]) if "organic" in product_name.lower() else False,
                        is_active=True,
                        created_at=datetime.now() - timedelta(days=random.randint(1, 365))
                    )
                    
                    products.append(product)
                    product_id_counter += 1
        
        # Add products to session
        self.session.add_all(products)
        self.session.flush()  # Get IDs
        
        self.products = products
        logger.info(f"Generated {len(products)} products")
        return products
    
    def _calculate_weight(self, unit: str) -> int:
        """Calculate approximate weight in grams based on unit."""
        unit_weights = {
            "kg": 1000,
            "1L": 1000,
            "400g": 400,
            "200g": 200,
            "100g": 100,
            "piece": 200,  # Average piece weight
            "dozen": 600,  # Average dozen weight
            "bunch": 100,  # Average bunch weight
            "pack": 150,   # Average pack weight
            "bottle": 500, # Average bottle weight
        }
        return unit_weights.get(unit, 250)  # Default 250g
    
    def generate_pricing_data(self) -> List[CurrentPrice]:
        """Generate realistic pricing data with platform variations."""
        logger.info("Generating pricing data with platform variations...")
        
        current_prices = []
        
        for product in self.products:
            # Get base price from template
            base_price = self._get_base_price(product.name)
            
            for platform in self.platforms:
                # Apply platform-specific pricing variation
                variation = PLATFORM_PRICING_VARIATIONS.get(platform.name, {"min": 0.95, "max": 1.15, "avg_discount": 10})
                
                # Calculate platform-specific price
                price_multiplier = random.uniform(variation["min"], variation["max"])
                platform_price = Decimal(str(base_price * price_multiplier)).quantize(Decimal('0.01'))
                
                # Determine if product has discount
                has_discount = random.random() < 0.3  # 30% chance of discount
                discount_percentage = None
                original_price = None
                
                if has_discount:
                    discount_percentage = random.randint(5, variation["avg_discount"] * 2)
                    original_price = platform_price
                    platform_price = platform_price * (1 - Decimal(discount_percentage) / 100)
                    platform_price = platform_price.quantize(Decimal('0.01'))
                
                # Create current price entry
                current_price = CurrentPrice(
                    product_id=product.id,
                    platform_id=platform.id,
                    price=platform_price,
                    original_price=original_price,
                    discount_percentage=discount_percentage,
                    is_available=random.choice([True, True, True, False]),  # 75% availability
                    stock_status=random.choice(['in_stock', 'in_stock', 'low_stock', 'out_of_stock']),
                    delivery_time_minutes=random.randint(10, 30),
                    minimum_order_quantity=1,
                    maximum_order_quantity=random.randint(5, 20),
                    price_per_unit=platform_price / Decimal(str(self._get_unit_quantity(product.pack_size))),
                    unit_type=product.pack_size,
                    last_updated=datetime.now() - timedelta(minutes=random.randint(1, 60))
                )
                
                current_prices.append(current_price)
        
        # Add to session
        self.session.add_all(current_prices)
        logger.info(f"Generated {len(current_prices)} current price entries")
        return current_prices
    
    def _get_base_price(self, product_name: str) -> float:
        """Get base price for a product based on its name."""
        for category_products in PRODUCT_TEMPLATES.values():
            for template in category_products:
                if template["name"].lower() in product_name.lower():
                    return template["base_price"]
        return 50.0  # Default price
    
    def _get_unit_quantity(self, unit_type: str) -> float:
        """Get quantity for unit calculations."""
        if "kg" in unit_type:
            return 1.0
        elif "L" in unit_type:
            return 1.0
        elif "g" in unit_type:
            return float(unit_type.replace('g', '')) / 1000
        else:
            return 1.0
    
    def generate_discount_data(self) -> List[Discount]:
        """Generate realistic discount and promotional data."""
        logger.info("Generating discount and promotional data...")
        
        discounts = []
        
        for platform in self.platforms:
            # Generate platform-wide discounts
            for template in DISCOUNT_TEMPLATES:
                # Random chance for each discount type
                if random.random() < 0.4:  # 40% chance for each discount
                    start_date = datetime.now() - timedelta(days=random.randint(0, 5))
                    end_date = start_date + timedelta(days=random.randint(7, 30))
                    
                    discount = Discount(
                        platform_id=platform.id,
                        discount_type=template["type"],
                        discount_value=Decimal(str(template["value"])),
                        discount_percentage=Decimal(str(template["value"])) if template["type"] == "percentage" else None,
                        min_order_amount=Decimal(str(template["min_order"])),
                        title=f"{platform.display_name} - {template['title']}",
                        description=f"Exclusive {template['title'].lower()} for {platform.display_name} customers",
                        is_active=start_date <= datetime.now() <= end_date,
                        is_featured=random.choice([True, False]),
                        start_date=start_date,
                        end_date=end_date,
                        usage_limit_per_user=random.randint(1, 5),
                        total_usage_limit=random.randint(100, 1000),
                        current_usage_count=random.randint(0, 50)
                    )
                    
                    discounts.append(discount)
            
            # Generate category-specific discounts
            for category in random.sample(self.categories, min(3, len(self.categories))):
                if random.random() < 0.3:  # 30% chance for category discount
                    discount_pct = random.randint(15, 40)
                    start_date = datetime.now() - timedelta(days=random.randint(0, 3))
                    end_date = start_date + timedelta(days=random.randint(3, 14))
                    
                    discount = Discount(
                        platform_id=platform.id,
                        category_id=category.id,
                        discount_type="percentage",
                        discount_value=Decimal(str(discount_pct)),
                        discount_percentage=Decimal(str(discount_pct)),
                        title=f"{discount_pct}% Off on {category.name}",
                        description=f"Special {discount_pct}% discount on all {category.name.lower()} items",
                        is_active=start_date <= datetime.now() <= end_date,
                        is_featured=discount_pct >= 25,
                        start_date=start_date,
                        end_date=end_date,
                        usage_limit_per_user=3,
                        total_usage_limit=500,
                        current_usage_count=random.randint(0, 100)
                    )
                    
                    discounts.append(discount)
        
        # Add to session
        self.session.add_all(discounts)
        logger.info(f"Generated {len(discounts)} discount entries")
        return discounts
    
    def generate_promotional_campaigns(self) -> List[PromotionalCampaign]:
        """Generate promotional campaigns with time-based variations."""
        logger.info("Generating promotional campaigns...")
        
        campaigns = []
        
        for platform in self.platforms:
            # Generate 2-3 campaigns per platform
            for template in random.sample(CAMPAIGN_TEMPLATES, random.randint(2, 3)):
                start_date = datetime.now() + timedelta(hours=random.randint(-24, 48))
                end_date = start_date + timedelta(hours=template["duration_hours"])
                
                campaign = PromotionalCampaign(
                    platform_id=platform.id,
                    campaign_name=f"{platform.display_name} {template['name']}",
                    campaign_slug=f"{platform.name}-{template['name'].lower().replace(' ', '-')}",
                    campaign_type=template["type"],
                    description=f"Exclusive {template['name']} campaign for {platform.display_name} customers with amazing deals and discounts",
                    target_audience=random.choice(["all_users", "new_users", "premium_users"]),
                    min_order_amount=Decimal(str(random.choice([200, 300, 500]))),
                    max_discount_amount=Decimal(str(random.choice([100, 200, 300]))),
                    usage_limit_per_user=random.randint(1, 3),
                    total_usage_limit=random.randint(500, 2000),
                    current_usage_count=random.randint(0, 100),
                    priority=random.randint(1, 5),
                    is_active=start_date <= datetime.now() <= end_date,
                    is_featured=random.choice([True, False]),
                    start_date=start_date,
                    end_date=end_date
                )
                
                campaigns.append(campaign)
        
        # Add to session
        self.session.add_all(campaigns)
        self.session.flush()  # Get IDs
        
        # Generate campaign products
        self._generate_campaign_products(campaigns)
        
        logger.info(f"Generated {len(campaigns)} promotional campaigns")
        return campaigns
    
    def _generate_campaign_products(self, campaigns: List[PromotionalCampaign]):
        """Generate products for promotional campaigns."""
        campaign_products = []
        
        for campaign in campaigns:
            # Add 5-15 products to each campaign
            selected_products = random.sample(self.products, min(random.randint(5, 15), len(self.products)))
            
            for i, product in enumerate(selected_products):
                discount_pct = random.randint(20, 50)
                
                campaign_product = CampaignProduct(
                    campaign_id=campaign.id,
                    product_id=product.id,
                    discount_percentage=Decimal(str(discount_pct)),
                    stock_allocated=random.randint(50, 200),
                    stock_sold=random.randint(0, 30),
                    display_order=i,
                    is_featured=i < 3  # First 3 products are featured
                )
                
                campaign_products.append(campaign_product)
        
        self.session.add_all(campaign_products)
        logger.info(f"Generated {len(campaign_products)} campaign product entries")
    
    def generate_inventory_data(self) -> List[InventoryLevel]:
        """Generate realistic inventory levels."""
        logger.info("Generating inventory data...")
        
        inventory_levels = []
        
        for product in self.products:
            for platform in self.platforms:
                # Generate realistic stock levels
                current_stock = random.randint(0, 500)
                reserved_stock = random.randint(0, min(current_stock, 50))
                available_stock = current_stock - reserved_stock
                
                inventory = InventoryLevel(
                    product_id=product.id,
                    platform_id=platform.id,
                    current_stock=current_stock,
                    reserved_stock=reserved_stock,
                    available_stock=available_stock,
                    reorder_level=random.randint(10, 50),
                    max_stock_level=random.randint(500, 1000),
                    stock_unit='pieces',
                    cost_per_unit=Decimal(str(random.uniform(10, 100))).quantize(Decimal('0.01'))
                )
                
                inventory_levels.append(inventory)
        
        self.session.add_all(inventory_levels)
        logger.info(f"Generated {len(inventory_levels)} inventory entries")
        return inventory_levels
    
    def generate_all_data(self, products_per_category: int = 8):
        """Generate all dummy data."""
        logger.info("Starting comprehensive dummy data generation...")
        
        # Load existing data
        self.load_existing_data()
        
        if not self.platforms:
            logger.error("No platforms found. Please run setup_core_tables.py first.")
            return False
        
        # Generate products
        self.generate_products(products_per_category)
        
        # Generate pricing data
        self.generate_pricing_data()
        
        # Generate discount data
        self.generate_discount_data()
        
        # Generate promotional campaigns
        self.generate_promotional_campaigns()
        
        # Generate inventory data
        self.generate_inventory_data()
        
        logger.info("✅ Dummy data generation completed successfully!")
        return True


def main():
    """Main function to generate dummy data."""
    try:
        with DummyDataGenerator() as generator:
            success = generator.generate_all_data(products_per_category=8)
            
            if success:
                logger.info("\n🎉 Data Generation Summary:")
                logger.info("📦 Generated realistic product catalog with variations")
                logger.info("💰 Created platform-specific pricing with realistic variations")
                logger.info("🏷️  Added discount and promotional data with time-based variations")
                logger.info("📊 Generated inventory levels for all products")
                logger.info("\n🚀 Ready for price comparison queries!")
                return True
            else:
                logger.error("❌ Data generation failed")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error during data generation: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)