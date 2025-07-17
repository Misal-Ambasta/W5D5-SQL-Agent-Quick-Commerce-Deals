#!/usr/bin/env python3
"""
Development database setup script
Creates SQLite database with sample data for testing
"""
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set environment to use SQLite
os.environ['DATABASE_URL'] = 'sqlite:///./quick_commerce_deals.db'
os.environ['USE_SQLITE'] = 'true'

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import models
from app.models.platform import Platform
from app.models.product import Product, ProductCategory, ProductBrand
from app.models.pricing import CurrentPrice, Discount, PromotionalCampaign
from app.core.database import Base

def create_database():
    """Create SQLite database and tables"""
    print("Creating SQLite database...")
    
    # Create engine
    engine = create_engine('sqlite:///./quick_commerce_deals.db', echo=True)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create platforms
        platforms = [
            Platform(
                name="Blinkit",
                display_name="Blinkit",
                api_endpoint="https://api.blinkit.com",
                website_url="https://blinkit.com",
                is_active=True,
                description="10-minute grocery delivery platform"
            ),
            Platform(
                name="Zepto",
                display_name="Zepto",
                api_endpoint="https://api.zepto.co.in",
                website_url="https://zepto.co.in",
                is_active=True,
                description="Fast grocery delivery service"
            ),
            Platform(
                name="Instamart",
                display_name="Swiggy Instamart",
                api_endpoint="https://api.swiggy.com/instamart",
                website_url="https://swiggy.com/instamart",
                is_active=True,
                description="Swiggy's quick commerce platform"
            ),
            Platform(
                name="BigBasket",
                display_name="BigBasket Now",
                api_endpoint="https://api.bigbasket.com/now",
                website_url="https://bigbasket.com",
                is_active=True,
                description="BigBasket's express delivery service"
            )
        ]
        
        for platform in platforms:
            db.add(platform)
        
        # Create categories
        categories = [
            ProductCategory(name="Vegetables", slug="vegetables", description="Fresh vegetables"),
            ProductCategory(name="Fruits", slug="fruits", description="Fresh fruits"),
            ProductCategory(name="Dairy", slug="dairy", description="Milk and dairy products"),
            ProductCategory(name="Grains", slug="grains", description="Rice, wheat, and other grains"),
            ProductCategory(name="Snacks", slug="snacks", description="Packaged snacks and chips"),
        ]
        
        for category in categories:
            db.add(category)
        
        # Create brands
        brands = [
            ProductBrand(name="Farm Fresh", slug="farm-fresh", description="Fresh produce brand"),
            ProductBrand(name="Amul", slug="amul", description="Dairy products"),
            ProductBrand(name="Tata", slug="tata", description="Consumer goods"),
            ProductBrand(name="Britannia", slug="britannia", description="Food products"),
            ProductBrand(name="Organic India", slug="organic-india", description="Organic products"),
        ]
        
        for brand in brands:
            db.add(brand)
        
        db.commit()
        
        # Get IDs for foreign keys
        veg_category = db.query(ProductCategory).filter_by(name="Vegetables").first()
        fruit_category = db.query(ProductCategory).filter_by(name="Fruits").first()
        dairy_category = db.query(ProductCategory).filter_by(name="Dairy").first()
        grains_category = db.query(ProductCategory).filter_by(name="Grains").first()
        
        farm_fresh_brand = db.query(ProductBrand).filter_by(name="Farm Fresh").first()
        amul_brand = db.query(ProductBrand).filter_by(name="Amul").first()
        tata_brand = db.query(ProductBrand).filter_by(name="Tata").first()
        
        # Create products
        products = [
            Product(
                name="Fresh Onions (1kg)",
                slug="fresh-onions-1kg",
                description="Fresh red onions",
                category_id=veg_category.id,
                brand_id=farm_fresh_brand.id,
                pack_size="1kg",
                is_organic=False,
                is_active=True
            ),
            Product(
                name="Tomatoes (1kg)",
                slug="tomatoes-1kg",
                description="Fresh tomatoes",
                category_id=veg_category.id,
                brand_id=farm_fresh_brand.id,
                pack_size="1kg",
                is_organic=False,
                is_active=True
            ),
            Product(
                name="Bananas (1kg)",
                slug="bananas-1kg",
                description="Fresh bananas",
                category_id=fruit_category.id,
                brand_id=farm_fresh_brand.id,
                pack_size="1kg",
                is_organic=False,
                is_active=True
            ),
            Product(
                name="Apples (1kg)",
                slug="apples-1kg",
                description="Fresh apples",
                category_id=fruit_category.id,
                brand_id=farm_fresh_brand.id,
                pack_size="1kg",
                is_organic=False,
                is_active=True
            ),
            Product(
                name="Milk (1L)",
                slug="milk-1l",
                description="Fresh milk",
                category_id=dairy_category.id,
                brand_id=amul_brand.id,
                pack_size="1L",
                is_organic=False,
                is_active=True
            ),
            Product(
                name="Basmati Rice (5kg)",
                slug="basmati-rice-5kg",
                description="Premium basmati rice",
                category_id=grains_category.id,
                brand_id=tata_brand.id,
                pack_size="5kg",
                is_organic=False,
                is_active=True
            ),
        ]
        
        for product in products:
            db.add(product)
        
        db.commit()
        
        # Create current prices
        platforms_list = db.query(Platform).all()
        products_list = db.query(Product).all()
        
        import random
        
        for product in products_list:
            base_price = random.uniform(20, 200)  # Random base price
            
            for platform in platforms_list:
                # Add some variation between platforms
                price_variation = random.uniform(0.8, 1.2)
                current_price = base_price * price_variation
                
                # Sometimes add discounts
                original_price = None
                discount_percentage = None
                
                if random.random() < 0.3:  # 30% chance of discount
                    discount_percentage = random.uniform(10, 40)
                    original_price = current_price / (1 - discount_percentage / 100)
                
                price_entry = CurrentPrice(
                    product_id=product.id,
                    platform_id=platform.id,
                    price=Decimal(str(round(current_price, 2))),
                    original_price=Decimal(str(round(original_price, 2))) if original_price else None,
                    discount_percentage=Decimal(str(round(discount_percentage, 2))) if discount_percentage else None,
                    is_available=random.choice([True, True, True, False]),  # 75% available
                    stock_status="in_stock" if random.random() > 0.2 else "low_stock",
                    delivery_time_minutes=random.randint(10, 30),
                    last_updated=datetime.now()
                )
                
                db.add(price_entry)
        
        # Create some sample discounts
        sample_discounts = [
            Discount(
                title="30% Off on Fresh Vegetables",
                description="Get 30% discount on all fresh vegetables",
                discount_type="percentage",
                discount_value=Decimal("30.00"),
                discount_percentage=Decimal("30.00"),
                platform_id=platforms_list[0].id,  # Blinkit
                category_id=veg_category.id,
                is_active=True,
                is_featured=True,
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now() + timedelta(days=7),
                usage_limit_per_user=5
            ),
            Discount(
                title="Buy 2 Get 1 Free on Fruits",
                description="Special offer on fresh fruits",
                discount_type="buy_x_get_y",
                discount_value=Decimal("33.33"),
                discount_percentage=Decimal("33.33"),
                platform_id=platforms_list[1].id,  # Zepto
                category_id=fruit_category.id,
                is_active=True,
                is_featured=False,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=5),
                usage_limit_per_user=3
            )
        ]
        
        for discount in sample_discounts:
            db.add(discount)
        
        db.commit()
        print("✅ Database created successfully with sample data!")
        
        # Print summary
        print(f"\nCreated:")
        print(f"- {len(platforms)} platforms")
        print(f"- {len(categories)} categories")
        print(f"- {len(brands)} brands")
        print(f"- {len(products)} products")
        print(f"- {len(platforms) * len(products)} price entries")
        print(f"- {len(sample_discounts)} sample discounts")
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_database()