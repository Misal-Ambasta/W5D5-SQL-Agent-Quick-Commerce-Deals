"""
Test script for sample query handlers implementation.
Tests the specific sample queries required in task 8.1.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import SessionLocal
from app.services.sample_query_handlers import get_sample_query_handlers


async def test_sample_queries():
    """Test all sample query handlers."""
    print("Testing Sample Query Handlers")
    print("=" * 50)
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Get sample query handlers
        handlers = get_sample_query_handlers()
        
        # Test queries as specified in requirements
        test_queries = [
            # Requirement 10.1: Cheapest product query
            "Which app has cheapest onions right now?",
            
            # Requirement 10.2: Discount query
            "Show products with 30%+ discount on Blinkit",
            
            # Requirement 10.3: Price comparison query
            "Compare fruit prices between Zepto and Instamart",
            
            # Requirement 10.4: Budget optimization query
            "Find best deals for ₹1000 grocery list"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Testing query: '{query}'")
            print("-" * 60)
            
            try:
                if "cheapest" in query.lower():
                    results = await handlers.handle_cheapest_product_query(db, query)
                elif "discount" in query.lower() or "%" in query.lower():
                    results = await handlers.handle_discount_query(db, query)
                elif "compare" in query.lower():
                    results = await handlers.handle_price_comparison_query(db, query)
                elif any(word in query.lower() for word in ["₹", "rs", "rupees", "budget", "grocery list", "deals for"]):
                    results = await handlers.handle_budget_optimization_query(db, query)
                else:
                    results = []
                
                print(f"Results found: {len(results)}")
                
                # Display first few results
                for j, result in enumerate(results[:3]):
                    print(f"  {j+1}. {result.product_name} - {result.platform_name}: ₹{result.current_price}")
                    if result.discount_percentage:
                        print(f"     Discount: {result.discount_percentage}%")
                
                if len(results) > 3:
                    print(f"  ... and {len(results) - 3} more results")
                
                if not results:
                    print("  No results found - this might be expected if database is empty")
                
            except Exception as e:
                print(f"  Error: {str(e)}")
        
        print(f"\n{'='*50}")
        print("Sample query testing completed!")
        
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        print("Make sure the database is running and contains test data")
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_sample_queries())