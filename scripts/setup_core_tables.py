#!/usr/bin/env python3
"""
Script to set up core platform and product tables for Quick Commerce Deals platform.
This script implements task 2.1 requirements.
"""

import sys
import os
import logging

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.migrations import create_core_tables, seed_initial_data

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """
    Main function to set up core database tables.
    """
    try:
        logger.info("Starting core table setup for Quick Commerce Deals platform...")
        
        # Create core platform and product tables
        logger.info("Step 1: Creating core platform and product tables...")
        create_core_tables()
        
        # Seed initial data
        logger.info("Step 2: Seeding initial platform and category data...")
        seed_initial_data()
        
        logger.info("✅ Core table setup completed successfully!")
        logger.info("\nCreated tables:")
        logger.info("📋 Platform tables:")
        logger.info("  - platforms (main platform information)")
        logger.info("  - platform_categories (platform-specific categories)")
        logger.info("  - platform_regions (geographic coverage)")
        logger.info("  - platform_delivery_zones (delivery areas)")
        logger.info("\n📦 Product tables:")
        logger.info("  - product_categories (hierarchical categories)")
        logger.info("  - product_subcategories (detailed subcategories)")
        logger.info("  - product_brands (brand information)")
        logger.info("  - products (master product catalog)")
        logger.info("  - product_variants (size/weight variants)")
        logger.info("  - product_attributes (nutritional info, etc.)")
        logger.info("  - product_images (product images)")
        logger.info("  - product_keywords (search optimization)")
        logger.info("  - product_synonyms (alternative names)")
        logger.info("\n🚀 Performance optimizations:")
        logger.info("  - Created indexes on frequently queried columns")
        logger.info("  - Added composite indexes for complex queries")
        logger.info("  - Implemented full-text search indexes")
        logger.info("  - Set up proper foreign key relationships")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during core table setup: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)