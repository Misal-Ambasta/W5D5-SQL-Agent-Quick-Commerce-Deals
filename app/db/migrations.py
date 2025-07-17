"""
Database migration scripts for Quick Commerce Deals platform.
"""

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from app.db.database import engine, Base
import logging

# Import ALL models to ensure they're registered with Base
# This is crucial - models must be imported before Base.metadata.create_all()
from app.models.platform import Platform, PlatformCategory, PlatformRegion, PlatformDeliveryZone
from app.models.product import (
    ProductCategory, ProductSubcategory, ProductBrand, Product, 
    ProductVariant, ProductAttribute, ProductImage, ProductKeyword, ProductSynonym
)
from app.models.pricing import (
    CurrentPrice, PriceHistory, Discount, PromotionalCampaign, CampaignProduct,
    BulkPricing, MembershipPrice, SurgePrice
)
from app.models.inventory import (
    InventoryLevel, AvailabilityStatus, StockAlert, DeliveryEstimate, 
    ServiceArea, InventoryHistory
)
from app.models.analytics import (
    QueryLog, PerformanceMetric, ApiUsageStats, ErrorLog, UserBehaviorAnalytics,
    PlatformPerformance, SearchAnalytics, CacheMetrics
)
from app.models.geographic import (
    City, PostalCode, DeliverySlot, WarehouseLocation, 
    DeliveryPartner, PlatformDeliveryPartner
)
from app.models.user import (
    User, UserPreference, SearchHistory, PriceAlert, ShoppingList, 
    ShoppingListItem, ComparisonHistory, UserSession, NotificationLog
)
from app.db.triggers import create_all_pricing_triggers
import logging

logger = logging.getLogger(__name__)


def create_core_tables():
    """
    Create core platform and product tables with proper relationships and indexes.
    This implements task 2.1 requirements.
    """
    try:
        logger.info("Creating core platform and product tables...")
        
        # Ensure all models are imported and registered with Base
        logger.info(f"Found {len(Base.metadata.tables)} tables to create")
        logger.info(f"Table names: {list(Base.metadata.tables.keys())}")
        
        # Check if Base has the expected tables
        expected_core_tables = ['platforms', 'platform_categories', 'platform_regions', 'platform_delivery_zones',
                               'product_categories', 'product_subcategories', 'product_brands', 'products',
                               'product_variants', 'product_attributes', 'product_images', 'product_keywords', 'product_synonyms']
        
        missing_tables = [table for table in expected_core_tables if table not in Base.metadata.tables]
        if missing_tables:
            logger.error(f"Missing expected tables in Base.metadata: {missing_tables}")
            logger.error("This indicates model import issues. Check that all models are properly imported.")
            return False
        
        # Create all tables defined in the models with explicit transaction
        with engine.begin() as conn:
            Base.metadata.create_all(bind=conn)
            logger.info("Table creation SQL executed successfully")
        
        # Verify tables were actually created in database
        with engine.connect() as conn:
            result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"))
            created_tables = [row[0] for row in result]
            logger.info(f"Tables found in database: {created_tables}")
            
            # Check if core tables were created
            core_tables_created = [table for table in expected_core_tables if table in created_tables]
            core_tables_missing = [table for table in expected_core_tables if table not in created_tables]
            
            if core_tables_missing:
                logger.error(f"Core tables not created in database: {core_tables_missing}")
                return False
            
            logger.info(f"Successfully verified {len(core_tables_created)} core tables in database")
        
        logger.info("Successfully created core tables:")
        logger.info("- Platform tables: platforms, platform_categories, platform_regions, platform_delivery_zones")
        logger.info("- Product tables: product_categories, product_subcategories, product_brands, products")
        logger.info("- Product detail tables: product_variants, product_attributes, product_images, product_keywords, product_synonyms")
        
        # Create indexes only if tables exist
        if created_tables:
            create_additional_indexes()
        else:
            logger.warning("No tables were created, skipping index creation")
        
        logger.info("Core table creation completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating core tables: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False


def create_additional_indexes():
    """
    Create additional performance indexes for frequently queried columns.
    """
    try:
        with engine.connect() as conn:
            # Additional composite indexes for complex queries
            indexes = [
                # Platform performance indexes
                "CREATE INDEX IF NOT EXISTS idx_platforms_name_active ON platforms(name, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_platform_categories_platform_parent ON platform_categories(platform_id, parent_category_id)",
                "CREATE INDEX IF NOT EXISTS idx_platform_regions_country_city ON platform_regions(country_code, city_name)",
                
                # Product search and filtering indexes
                "CREATE INDEX IF NOT EXISTS idx_products_search ON products USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')))",
                "CREATE INDEX IF NOT EXISTS idx_products_brand_category_active ON products(brand_id, category_id, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_product_categories_parent_level ON product_categories(parent_id, level)",
                "CREATE INDEX IF NOT EXISTS idx_product_brands_name_active ON product_brands(name, is_active)",
                
                # Product detail indexes for fast lookups
                "CREATE INDEX IF NOT EXISTS idx_product_variants_product_default ON product_variants(product_id, is_default)",
                "CREATE INDEX IF NOT EXISTS idx_product_attributes_type_searchable ON product_attributes(attribute_type, is_searchable)",
                "CREATE INDEX IF NOT EXISTS idx_product_images_product_primary ON product_images(product_id, is_primary)",
                "CREATE INDEX IF NOT EXISTS idx_product_keywords_relevance ON product_keywords(keyword, relevance_score DESC)",
                
                # Text search indexes
                "CREATE INDEX IF NOT EXISTS idx_product_synonyms_search ON product_synonyms USING gin(to_tsvector('english', synonym))",
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    conn.commit()  # Commit each index creation separately
                    logger.info(f"Created index: {index_sql.split('idx_')[1].split(' ')[0] if 'idx_' in index_sql else 'custom'}")
                except Exception as e:
                    conn.rollback()  # Rollback failed transaction
                    logger.warning(f"Index creation warning: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error creating additional indexes: {str(e)}")
        raise


def seed_initial_data():
    """
    Seed initial data for platforms and basic categories.
    """
    from sqlalchemy.orm import sessionmaker
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if data already exists
        if session.query(Platform).count() > 0:
            logger.info("Initial data already exists, skipping seed")
            return
        
        # Seed platforms
        platforms = [
            Platform(
                name="blinkit",
                display_name="Blinkit",
                api_endpoint="https://api.blinkit.com",
                website_url="https://blinkit.com",
                description="10-minute grocery delivery platform"
            ),
            Platform(
                name="zepto",
                display_name="Zepto",
                api_endpoint="https://api.zepto.co.in",
                website_url="https://zepto.co.in",
                description="Fast grocery delivery service"
            ),
            Platform(
                name="instamart",
                display_name="Swiggy Instamart",
                api_endpoint="https://api.swiggy.com/instamart",
                website_url="https://swiggy.com/instamart",
                description="Swiggy's quick commerce platform"
            ),
            Platform(
                name="bigbasket_now",
                display_name="BigBasket Now",
                api_endpoint="https://api.bigbasket.com/now",
                website_url="https://bigbasket.com",
                description="BigBasket's express delivery service"
            ),
            Platform(
                name="dunzo",
                display_name="Dunzo",
                api_endpoint="https://api.dunzo.com",
                website_url="https://dunzo.com",
                description="Hyperlocal delivery platform"
            )
        ]
        
        session.add_all(platforms)
        session.flush()  # Get IDs
        
        # Seed basic product categories
        categories = [
            ProductCategory(name="Fruits & Vegetables", slug="fruits-vegetables", level=0, display_order=1),
            ProductCategory(name="Dairy & Eggs", slug="dairy-eggs", level=0, display_order=2),
            ProductCategory(name="Meat & Seafood", slug="meat-seafood", level=0, display_order=3),
            ProductCategory(name="Pantry Staples", slug="pantry-staples", level=0, display_order=4),
            ProductCategory(name="Snacks & Beverages", slug="snacks-beverages", level=0, display_order=5),
            ProductCategory(name="Personal Care", slug="personal-care", level=0, display_order=6),
            ProductCategory(name="Household Items", slug="household-items", level=0, display_order=7),
            ProductCategory(name="Baby Care", slug="baby-care", level=0, display_order=8),
        ]
        
        session.add_all(categories)
        session.flush()
        
        # Add subcategories for Fruits & Vegetables
        fruits_veg_cat = session.query(ProductCategory).filter_by(slug="fruits-vegetables").first()
        subcategories = [
            ProductCategory(name="Fresh Fruits", slug="fresh-fruits", parent_id=fruits_veg_cat.id, level=1, display_order=1),
            ProductCategory(name="Fresh Vegetables", slug="fresh-vegetables", parent_id=fruits_veg_cat.id, level=1, display_order=2),
            ProductCategory(name="Herbs & Seasonings", slug="herbs-seasonings", parent_id=fruits_veg_cat.id, level=1, display_order=3),
        ]
        
        session.add_all(subcategories)
        
        # Seed basic brands
        brands = [
            ProductBrand(name="Amul", slug="amul", description="India's leading dairy brand"),
            ProductBrand(name="Britannia", slug="britannia", description="Popular food and bakery brand"),
            ProductBrand(name="Nestle", slug="nestle", description="Global food and beverage company"),
            ProductBrand(name="Tata", slug="tata", description="Tata consumer products"),
            ProductBrand(name="ITC", slug="itc", description="ITC consumer goods"),
            ProductBrand(name="Organic India", slug="organic-india", description="Organic food products"),
            ProductBrand(name="Fresh", slug="fresh", description="Fresh produce brand"),
        ]
        
        session.add_all(brands)
        session.commit()
        
        logger.info("Successfully seeded initial data:")
        logger.info(f"- {len(platforms)} platforms")
        logger.info(f"- {len(categories) + len(subcategories)} product categories")
        logger.info(f"- {len(brands)} brands")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error seeding initial data: {str(e)}")
        raise
    finally:
        session.close()


def create_pricing_tables():
    """
    Create pricing and discount tables with proper relationships and indexes.
    This implements task 2.2 requirements.
    """
    try:
        logger.info("Creating pricing and discount tables...")
        
        # Create all tables (this will include pricing tables)
        Base.metadata.create_all(bind=engine)
        
        logger.info("Successfully created pricing tables:")
        logger.info("- current_prices (real-time pricing data)")
        logger.info("- price_history (historical price tracking)")
        logger.info("- discounts (active discount information)")
        logger.info("- promotional_campaigns (marketing campaigns)")
        logger.info("- campaign_products (products in campaigns)")
        logger.info("- bulk_pricing (quantity-based pricing)")
        logger.info("- membership_prices (platform-specific member pricing)")
        logger.info("- surge_prices (dynamic pricing during high demand)")
        
        # Create pricing-specific indexes
        create_pricing_indexes()
        
        # Create triggers for automatic price history tracking
        create_all_pricing_triggers()
        
        logger.info("Pricing table creation completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating pricing tables: {str(e)}")
        raise


def create_pricing_indexes():
    """
    Create additional performance indexes for pricing queries.
    """
    try:
        with engine.connect() as conn:
            # Pricing-specific indexes for performance optimization
            pricing_indexes = [
                # Current prices indexes for fast price lookups
                "CREATE INDEX IF NOT EXISTS idx_current_prices_product_available ON current_prices(product_id, is_available)",
                "CREATE INDEX IF NOT EXISTS idx_current_prices_platform_available ON current_prices(platform_id, is_available)",
                "CREATE INDEX IF NOT EXISTS idx_current_prices_price_range ON current_prices(price) WHERE is_available = true",
                "CREATE INDEX IF NOT EXISTS idx_current_prices_discount_range ON current_prices(discount_percentage) WHERE discount_percentage > 0",
                "CREATE INDEX IF NOT EXISTS idx_current_prices_updated_recent ON current_prices(last_updated DESC) WHERE is_available = true",
                
                # Price history indexes for trend analysis
                "CREATE INDEX IF NOT EXISTS idx_price_history_product_date ON price_history(product_id, recorded_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_price_history_platform_date ON price_history(platform_id, recorded_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_price_history_change_type ON price_history(price_change_type, recorded_at DESC)",
                
                # Discount indexes for deal queries
                "CREATE INDEX IF NOT EXISTS idx_discounts_active_dates ON discounts(is_active, start_date, end_date) WHERE is_active = true",
                "CREATE INDEX IF NOT EXISTS idx_discounts_platform_active ON discounts(platform_id, is_active) WHERE is_active = true",
                "CREATE INDEX IF NOT EXISTS idx_discounts_product_active ON discounts(product_id, is_active) WHERE product_id IS NOT NULL AND is_active = true",
                "CREATE INDEX IF NOT EXISTS idx_discounts_category_active ON discounts(category_id, is_active) WHERE category_id IS NOT NULL AND is_active = true",
                "CREATE INDEX IF NOT EXISTS idx_discounts_percentage_high ON discounts(discount_percentage DESC) WHERE discount_percentage >= 30",
                "CREATE INDEX IF NOT EXISTS idx_discounts_featured ON discounts(is_featured, discount_percentage DESC) WHERE is_featured = true",
                
                # Campaign indexes
                "CREATE INDEX IF NOT EXISTS idx_campaigns_active_dates ON promotional_campaigns(is_active, start_date, end_date) WHERE is_active = true",
                "CREATE INDEX IF NOT EXISTS idx_campaigns_platform_type ON promotional_campaigns(platform_id, campaign_type, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_campaigns_featured ON promotional_campaigns(is_featured, priority DESC) WHERE is_featured = true",
                
                # Campaign products indexes
                "CREATE INDEX IF NOT EXISTS idx_campaign_products_campaign ON campaign_products(campaign_id, display_order)",
                "CREATE INDEX IF NOT EXISTS idx_campaign_products_product ON campaign_products(product_id)",
                "CREATE INDEX IF NOT EXISTS idx_campaign_products_featured ON campaign_products(is_featured, display_order) WHERE is_featured = true",
                
                # Bulk pricing indexes
                "CREATE INDEX IF NOT EXISTS idx_bulk_pricing_product_quantity ON bulk_pricing(product_id, min_quantity)",
                "CREATE INDEX IF NOT EXISTS idx_bulk_pricing_platform_active ON bulk_pricing(platform_id, is_active) WHERE is_active = true",
                
                # Membership pricing indexes
                "CREATE INDEX IF NOT EXISTS idx_membership_prices_product_type ON membership_prices(product_id, membership_type)",
                "CREATE INDEX IF NOT EXISTS idx_membership_prices_platform_type ON membership_prices(platform_id, membership_type)",
                "CREATE INDEX IF NOT EXISTS idx_membership_prices_savings ON membership_prices(savings_percentage DESC) WHERE is_active = true",
                
                # Surge pricing indexes
                "CREATE INDEX IF NOT EXISTS idx_surge_prices_active_time ON surge_prices(is_active, start_time, end_time) WHERE is_active = true",
                "CREATE INDEX IF NOT EXISTS idx_surge_prices_product_platform ON surge_prices(product_id, platform_id, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_surge_prices_multiplier ON surge_prices(surge_multiplier DESC) WHERE is_active = true",
            ]
            
            for index_sql in pricing_indexes:
                try:
                    conn.execute(text(index_sql))
                    index_name = index_sql.split('idx_')[1].split(' ')[0] if 'idx_' in index_sql else 'custom'
                    logger.info(f"Created pricing index: {index_name}")
                except Exception as e:
                    logger.warning(f"Pricing index creation warning: {str(e)}")
            
            conn.commit()
            
    except Exception as e:
        logger.error(f"Error creating pricing indexes: {str(e)}")
        raise


def seed_pricing_data():
    """
    Seed sample pricing and discount data for testing.
    """
    from sqlalchemy.orm import sessionmaker
    from decimal import Decimal
    from datetime import datetime, timedelta
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if pricing data already exists
        if session.query(CurrentPrice).count() > 0:
            logger.info("Pricing data already exists, skipping seed")
            return
        
        # Get some platforms and products for seeding
        platforms = session.query(Platform).limit(3).all()
        products = session.query(Product).limit(10).all()
        
        if not platforms or not products:
            logger.warning("No platforms or products found, skipping pricing data seed")
            return
        
        # Create sample current prices
        current_prices = []
        for product in products:
            for platform in platforms:
                base_price = Decimal('50.00') + (product.id * Decimal('10.00'))
                discount_pct = (product.id % 4) * 5  # 0%, 5%, 10%, 15% discounts
                
                if discount_pct > 0:
                    original_price = base_price
                    discounted_price = base_price * (1 - Decimal(discount_pct) / 100)
                else:
                    original_price = None
                    discounted_price = base_price
                    discount_pct = None
                
                current_price = CurrentPrice(
                    product_id=product.id,
                    platform_id=platform.id,
                    price=discounted_price,
                    original_price=original_price,
                    discount_percentage=discount_pct,
                    is_available=True,
                    stock_status='in_stock',
                    delivery_time_minutes=15 + (platform.id * 5)
                )
                current_prices.append(current_price)
        
        session.add_all(current_prices)
        session.flush()
        
        # Create sample discounts
        discounts = []
        for i, platform in enumerate(platforms):
            # Platform-wide discount
            discount = Discount(
                platform_id=platform.id,
                discount_type='percentage',
                discount_value=Decimal('20.00'),
                discount_percentage=Decimal('20.00'),
                title=f'{platform.display_name} Special Offer',
                description=f'Get 20% off on all products on {platform.display_name}',
                is_active=True,
                is_featured=i == 0,  # Make first platform featured
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now() + timedelta(days=30)
            )
            discounts.append(discount)
        
        session.add_all(discounts)
        
        # Create sample promotional campaign
        campaign = PromotionalCampaign(
            platform_id=platforms[0].id,
            campaign_name='Flash Sale Weekend',
            campaign_slug='flash-sale-weekend',
            campaign_type='flash_sale',
            description='Weekend flash sale with up to 50% off on selected items',
            is_active=True,
            is_featured=True,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=3),
            priority=1
        )
        session.add(campaign)
        session.flush()
        
        # Add products to campaign
        campaign_products = []
        for i, product in enumerate(products[:5]):  # First 5 products
            campaign_product = CampaignProduct(
                campaign_id=campaign.id,
                product_id=product.id,
                discount_percentage=Decimal('30.00') + (i * Decimal('5.00')),
                stock_allocated=100,
                display_order=i,
                is_featured=i < 2
            )
            campaign_products.append(campaign_product)
        
        session.add_all(campaign_products)
        session.commit()
        
        logger.info("Successfully seeded pricing data:")
        logger.info(f"- {len(current_prices)} current prices")
        logger.info(f"- {len(discounts)} discounts")
        logger.info(f"- 1 promotional campaign with {len(campaign_products)} products")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error seeding pricing data: {str(e)}")
        raise
    finally:
        session.close()


def create_inventory_analytics_tables():
    """
    Create inventory and analytics tables to reach 50+ table requirement.
    This implements task 2.3 requirements.
    """
    try:
        logger.info("Creating inventory and analytics tables...")
        
        # Create all tables (this will include all remaining tables)
        Base.metadata.create_all(bind=engine)
        
        logger.info("Successfully created inventory tables:")
        logger.info("- inventory_levels (current stock levels)")
        logger.info("- availability_status (real-time availability)")
        logger.info("- stock_alerts (low stock notifications)")
        logger.info("- delivery_estimates (estimated delivery times)")
        logger.info("- service_areas (delivery coverage areas)")
        logger.info("- inventory_history (stock level changes)")
        
        logger.info("Successfully created analytics tables:")
        logger.info("- query_logs (SQL query execution logs)")
        logger.info("- performance_metrics (system performance data)")
        logger.info("- api_usage_stats (API endpoint usage)")
        logger.info("- error_logs (system error tracking)")
        logger.info("- user_behavior_analytics (user interaction patterns)")
        logger.info("- platform_performance (platform response metrics)")
        logger.info("- search_analytics (search query analytics)")
        logger.info("- cache_metrics (cache performance metrics)")
        
        logger.info("Successfully created geographic tables:")
        logger.info("- cities (supported city information)")
        logger.info("- postal_codes (delivery area mapping)")
        logger.info("- delivery_slots (available delivery times)")
        logger.info("- warehouse_locations (fulfillment centers)")
        logger.info("- delivery_partners (third-party delivery services)")
        logger.info("- platform_delivery_partners (platform-partner mapping)")
        
        logger.info("Successfully created user tables:")
        logger.info("- users (user account information)")
        logger.info("- user_preferences (shopping preferences)")
        logger.info("- search_history (user query patterns)")
        logger.info("- price_alerts (user price notifications)")
        logger.info("- shopping_lists (saved shopping lists)")
        logger.info("- shopping_list_items (items in lists)")
        logger.info("- comparison_history (price comparison history)")
        logger.info("- user_sessions (session tracking)")
        logger.info("- notification_logs (notification history)")
        
        # Create comprehensive database indexes
        create_comprehensive_indexes()
        
        logger.info("Inventory and analytics table creation completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating inventory and analytics tables: {str(e)}")
        raise


def create_comprehensive_indexes():
    """
    Create comprehensive database indexes for query optimization across all 50+ tables.
    """
    try:
        with engine.connect() as conn:
            # Comprehensive indexes for all table types
            comprehensive_indexes = [
                # Inventory table indexes
                "CREATE INDEX IF NOT EXISTS idx_inventory_levels_stock_alerts ON inventory_levels(available_stock, reorder_level) WHERE available_stock <= reorder_level",
                "CREATE INDEX IF NOT EXISTS idx_availability_status_platform_available ON availability_status(platform_id, is_available, last_checked DESC)",
                "CREATE INDEX IF NOT EXISTS idx_stock_alerts_urgent ON stock_alerts(alert_level, is_resolved, created_at DESC) WHERE alert_level IN ('critical', 'urgent')",
                "CREATE INDEX IF NOT EXISTS idx_delivery_estimates_postal_time ON delivery_estimates(postal_code, average_delivery_time)",
                "CREATE INDEX IF NOT EXISTS idx_service_areas_coordinates ON service_areas USING gist(coordinates) WHERE coordinates IS NOT NULL",
                "CREATE INDEX IF NOT EXISTS idx_inventory_history_value_changes ON inventory_history(total_value, recorded_at DESC) WHERE total_value IS NOT NULL",
                
                # Analytics table indexes
                "CREATE INDEX IF NOT EXISTS idx_query_logs_performance ON query_logs(execution_time_ms DESC, created_at DESC) WHERE execution_status = 'success'",
                "CREATE INDEX IF NOT EXISTS idx_performance_metrics_trends ON performance_metrics(metric_name, recorded_at DESC, metric_value)",
                "CREATE INDEX IF NOT EXISTS idx_api_usage_stats_errors ON api_usage_stats(status_code, created_at DESC) WHERE status_code >= 400",
                "CREATE INDEX IF NOT EXISTS idx_error_logs_critical ON error_logs(error_level, created_at DESC, is_resolved) WHERE error_level IN ('error', 'critical')",
                "CREATE INDEX IF NOT EXISTS idx_user_behavior_conversion ON user_behavior_analytics(event_type, created_at DESC) WHERE event_type IN ('purchase', 'add_to_cart')",
                "CREATE INDEX IF NOT EXISTS idx_platform_performance_sla ON platform_performance(platform_id, success, measured_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_search_analytics_popular ON search_analytics(normalized_query, search_date DESC, results_count DESC)",
                "CREATE INDEX IF NOT EXISTS idx_cache_metrics_efficiency ON cache_metrics(cache_type, hit_rate DESC, recorded_at DESC)",
                
                # Geographic table indexes
                "CREATE INDEX IF NOT EXISTS idx_cities_location ON cities(latitude, longitude) WHERE latitude IS NOT NULL AND longitude IS NOT NULL",
                "CREATE INDEX IF NOT EXISTS idx_postal_codes_location ON postal_codes(latitude, longitude) WHERE latitude IS NOT NULL AND longitude IS NOT NULL",
                "CREATE INDEX IF NOT EXISTS idx_delivery_slots_availability ON delivery_slots(platform_id, city_id, is_available, day_of_week)",
                "CREATE INDEX IF NOT EXISTS idx_warehouse_locations_coverage ON warehouse_locations(platform_id, city_id, warehouse_type, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_delivery_partners_performance ON delivery_partners(service_type, rating DESC, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_platform_delivery_partners_priority ON platform_delivery_partners(platform_id, city_id, priority_order, is_active)",
                
                # User table indexes
                "CREATE INDEX IF NOT EXISTS idx_users_location_active ON users(city_id, postal_code, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_user_preferences_personalization ON user_preferences(user_id, preference_type, priority, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_search_history_patterns ON search_history(user_id, query_type, search_success, created_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_price_alerts_active_monitoring ON price_alerts(is_active, alert_type, last_triggered) WHERE is_active = true",
                "CREATE INDEX IF NOT EXISTS idx_shopping_lists_recent ON shopping_lists(user_id, list_type, last_accessed DESC, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_shopping_list_items_pending ON shopping_list_items(shopping_list_id, is_purchased, priority) WHERE is_purchased = false",
                "CREATE INDEX IF NOT EXISTS idx_comparison_history_insights ON comparison_history(user_id, comparison_type, potential_savings DESC, created_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_user_sessions_analytics ON user_sessions(user_id, session_start DESC, duration_minutes DESC)",
                "CREATE INDEX IF NOT EXISTS idx_notification_logs_engagement ON notification_logs(user_id, notification_type, status, sent_at DESC)",
                
                # Cross-table optimization indexes
                "CREATE INDEX IF NOT EXISTS idx_products_full_search ON products USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '') || ' ' || COALESCE(short_description, '')))",
                "CREATE INDEX IF NOT EXISTS idx_current_prices_best_deals ON current_prices(discount_percentage DESC, price ASC) WHERE is_available = true AND discount_percentage > 0",
                "CREATE INDEX IF NOT EXISTS idx_discounts_active_high_value ON discounts(discount_percentage DESC, start_date, end_date) WHERE is_active = true AND discount_percentage >= 20",
                "CREATE INDEX IF NOT EXISTS idx_inventory_availability_cross ON inventory_levels(product_id, platform_id, available_stock DESC) WHERE available_stock > 0",
            ]
            
            for index_sql in comprehensive_indexes:
                try:
                    conn.execute(text(index_sql))
                    index_name = index_sql.split('idx_')[1].split(' ')[0] if 'idx_' in index_sql else 'custom'
                    logger.info(f"Created comprehensive index: {index_name}")
                except Exception as e:
                    logger.warning(f"Comprehensive index creation warning: {str(e)}")
            
            conn.commit()
            
    except Exception as e:
        logger.error(f"Error creating comprehensive indexes: {str(e)}")
        raise


def seed_comprehensive_data():
    """
    Seed sample data across all tables for testing and demonstration.
    """
    from sqlalchemy.orm import sessionmaker
    from decimal import Decimal
    from datetime import datetime, timedelta
    import random
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if comprehensive data already exists
        if session.query(City).count() > 0:
            logger.info("Comprehensive data already exists, skipping seed")
            return
        
        # Seed cities
        cities = [
            City(name="Mumbai", state_code="MH", state_name="Maharashtra", is_metro=True),
            City(name="Delhi", state_code="DL", state_name="Delhi", is_metro=True),
            City(name="Bangalore", state_code="KA", state_name="Karnataka", is_metro=True),
            City(name="Hyderabad", state_code="TG", state_name="Telangana", is_metro=True),
            City(name="Chennai", state_code="TN", state_name="Tamil Nadu", is_metro=True),
            City(name="Pune", state_code="MH", state_name="Maharashtra", is_metro=False),
            City(name="Kolkata", state_code="WB", state_name="West Bengal", is_metro=True),
            City(name="Ahmedabad", state_code="GJ", state_name="Gujarat", is_metro=False),
        ]
        session.add_all(cities)
        session.flush()
        
        # Seed postal codes
        postal_codes = []
        for city in cities:
            for i in range(3):  # 3 postal codes per city
                postal_code = PostalCode(
                    postal_code=f"{city.id:02d}{i+1:04d}",
                    city_id=city.id,
                    area_name=f"{city.name} Area {i+1}",
                    state_code=city.state_code,
                    delivery_zone=f"zone_{chr(65+i)}"  # zone_A, zone_B, zone_C
                )
                postal_codes.append(postal_code)
        session.add_all(postal_codes)
        session.flush()
        
        # Get existing platforms and products
        platforms = session.query(Platform).all()
        products = session.query(Product).all()
        
        if platforms and products and cities:
            # Seed warehouse locations
            warehouses = []
            for platform in platforms:
                for city in cities[:3]:  # First 3 cities
                    warehouse = WarehouseLocation(
                        platform_id=platform.id,
                        warehouse_name=f"{platform.display_name} {city.name} Hub",
                        warehouse_code=f"{platform.name.upper()}-{city.name.upper()[:3]}",
                        address_line1=f"Industrial Area, {city.name}",
                        city_id=city.id,
                        postal_code=postal_codes[city.id-1].postal_code,
                        warehouse_type="fulfillment",
                        is_active=True
                    )
                    warehouses.append(warehouse)
            session.add_all(warehouses)
            session.flush()
            
            # Seed inventory levels
            inventory_levels = []
            for product in products[:20]:  # First 20 products
                for platform in platforms:
                    stock_level = random.randint(50, 500)
                    inventory = InventoryLevel(
                        product_id=product.id,
                        platform_id=platform.id,
                        warehouse_id=warehouses[0].id if warehouses else None,
                        current_stock=stock_level,
                        available_stock=stock_level - random.randint(0, 10),
                        reorder_level=random.randint(20, 50),
                        cost_per_unit=Decimal(str(random.uniform(10.0, 100.0)))
                    )
                    inventory_levels.append(inventory)
            session.add_all(inventory_levels)
            
            # Seed availability status
            availability_statuses = []
            for product in products[:15]:  # First 15 products
                for platform in platforms:
                    availability = AvailabilityStatus(
                        product_id=product.id,
                        platform_id=platform.id,
                        is_available=random.choice([True, True, True, False]),  # 75% available
                        availability_status=random.choice(['available', 'low_stock', 'out_of_stock']),
                        delivery_available=True,
                        estimated_delivery_time=random.randint(15, 60)
                    )
                    availability_statuses.append(availability)
            session.add_all(availability_statuses)
            
        session.commit()
        
        logger.info("Successfully seeded comprehensive data:")
        logger.info(f"- {len(cities)} cities")
        logger.info(f"- {len(postal_codes)} postal codes")
        logger.info(f"- {len(warehouses) if 'warehouses' in locals() else 0} warehouses")
        logger.info(f"- {len(inventory_levels) if 'inventory_levels' in locals() else 0} inventory records")
        logger.info(f"- {len(availability_statuses) if 'availability_statuses' in locals() else 0} availability records")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error seeding comprehensive data: {str(e)}")
        raise
    finally:
        session.close()


def get_table_count():
    """
    Get the total number of tables created in the database.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) as table_count 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """))
            count = result.fetchone()[0]
            logger.info(f"Total tables created: {count}")
            return count
    except Exception as e:
        logger.error(f"Error getting table count: {str(e)}")
        return 0


def drop_all_tables():
    """
    Drop all tables in the database.
    """
    try:
        logger.warning("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping tables: {str(e)}")
        raise


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create core tables
    create_core_tables()
    
    # Seed initial data
    seed_initial_data()
    
    print("Core database schema setup completed successfully!")