#!/usr/bin/env python3
"""
Test script for product comparison functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.v1.endpoints.products import compare_products, _get_product_comparisons
from app.database import get_db
from app.core.exceptions import ProductNotFoundError
from sqlalchemy.orm import Session
import asyncio

async def test_product_comparison():
    """Test the product comparison functionality"""
    print("Testing product comparison functionality...")
    
    # Get database session
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        # Test with "milk" query that was causing 500 error
        print("\n1. Testing milk comparison...")
        try:
            result = await _get_product_comparisons(
                db=db,
                product_name="milk",
                platforms=[],
                category=None,
                brand=None
            )
            print(f"✅ Milk comparison successful: Found {len(result)} products")
            for product in result[:3]:  # Show first 3
                print(f"   - {product.product_name}: ₹{product.best_price} on {product.best_platform}")
        except ProductNotFoundError as e:
            print(f"ℹ️  No milk products found: {e.message}")
        except Exception as e:
            print(f"❌ Error with milk comparison: {str(e)}")
        
        # Test with "onions" query
        print("\n2. Testing onions comparison...")
        try:
            result = await _get_product_comparisons(
                db=db,
                product_name="onions",
                platforms=[],
                category=None,
                brand=None
            )
            print(f"✅ Onions comparison successful: Found {len(result)} products")
            for product in result[:3]:  # Show first 3
                print(f"   - {product.product_name}: ₹{product.best_price} on {product.best_platform}")
        except ProductNotFoundError as e:
            print(f"ℹ️  No onion products found: {e.message}")
        except Exception as e:
            print(f"❌ Error with onions comparison: {str(e)}")
        
        # Test with "bread" query
        print("\n3. Testing bread comparison...")
        try:
            result = await _get_product_comparisons(
                db=db,
                product_name="bread",
                platforms=[],
                category=None,
                brand=None
            )
            print(f"✅ Bread comparison successful: Found {len(result)} products")
            for product in result[:3]:  # Show first 3
                print(f"   - {product.product_name}: ₹{product.best_price} on {product.best_platform}")
        except ProductNotFoundError as e:
            print(f"ℹ️  No bread products found: {e.message}")
        except Exception as e:
            print(f"❌ Error with bread comparison: {str(e)}")
            
    finally:
        db.close()
    
    print("\n✅ Product comparison test completed!")

if __name__ == "__main__":
    asyncio.run(test_product_comparison())
