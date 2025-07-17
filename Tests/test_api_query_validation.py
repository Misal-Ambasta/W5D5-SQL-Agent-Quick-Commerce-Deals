"""
API Integration test for query accuracy validation.
Tests the query endpoints with validation integration.
"""

import asyncio
import sys
import os
import json
from fastapi.testclient import TestClient

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.main import app
from app.core.database import SessionLocal
from app.services.query_accuracy_validator import get_query_accuracy_validator


def test_api_query_validation():
    """Test API endpoints with query validation."""
    print("API Query Validation Integration Test")
    print("=" * 50)
    
    client = TestClient(app)
    
    # Test queries
    test_queries = [
        {
            "query": "Which app has cheapest onions right now?",
            "expected_status": 200,
            "min_results": 0
        },
        {
            "query": "Show products with 30%+ discount on Blinkit",
            "expected_status": 200,
            "min_results": 0
        },
        {
            "query": "Compare fruit prices between Zepto and Instamart",
            "expected_status": 200,
            "min_results": 0
        },
        {
            "query": "Find best deals for ₹1000 grocery list",
            "expected_status": 200,
            "min_results": 0
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n{i}. Testing API endpoint with: '{test_case['query']}'")
        print("-" * 60)
        
        try:
            # Make API request
            response = client.post(
                "/api/v1/query/",
                json={"query": test_case["query"]}
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == test_case["expected_status"]:
                print("   ✓ Status code matches expected")
                
                # Parse response
                data = response.json()
                
                print(f"   Results: {len(data.get('results', []))} products")
                print(f"   Execution time: {data.get('execution_time', 0):.3f}s")
                print(f"   Relevant tables: {data.get('relevant_tables', [])}")
                
                # Check minimum results
                if len(data.get('results', [])) >= test_case["min_results"]:
                    print("   ✓ Minimum result count satisfied")
                else:
                    print(f"   ⚠ Expected at least {test_case['min_results']} results")
                
                # Check response structure
                required_fields = ['query', 'results', 'execution_time', 'relevant_tables', 'total_results']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    print("   ✓ Response structure is complete")
                else:
                    print(f"   ❌ Missing fields: {missing_fields}")
                
                # Validate individual results if present
                if data.get('results'):
                    sample_result = data['results'][0]
                    result_fields = ['product_id', 'product_name', 'platform_name', 'current_price', 'is_available']
                    missing_result_fields = [field for field in result_fields if field not in sample_result]
                    
                    if not missing_result_fields:
                        print("   ✓ Result structure is complete")
                    else:
                        print(f"   ❌ Missing result fields: {missing_result_fields}")
                
            else:
                print(f"   ❌ Expected status {test_case['expected_status']}, got {response.status_code}")
                print(f"   Response: {response.text}")
        
        except Exception as e:
            print(f"   ❌ API test failed: {str(e)}")
    
    print(f"\n{'='*50}")
    print("API query validation testing completed!")


async def test_validation_integration():
    """Test direct integration with validation service."""
    print("\n\nDirect Validation Service Integration Test")
    print("=" * 50)
    
    db = SessionLocal()
    validator = get_query_accuracy_validator()
    
    try:
        # Import sample handlers
        from app.services.sample_query_handlers import get_sample_query_handlers
        handlers = get_sample_query_handlers()
        
        # Test query
        query = "Which app has cheapest onions right now?"
        
        print(f"Testing validation integration with: '{query}'")
        
        # Execute query
        start_time = asyncio.get_event_loop().time()
        results = await handlers.handle_cheapest_product_query(db, query)
        execution_time = asyncio.get_event_loop().time() - start_time
        
        print(f"Query executed: {len(results)} results in {execution_time:.3f}s")
        
        # Validate results
        validation_report = await validator.validate_query_results(
            query, results, "cheapest_product", execution_time, db
        )
        
        print(f"Validation completed: {validation_report.overall_status.value}")
        print(f"Validation rules executed: {len(validation_report.validation_results)}")
        print(f"Issues found: {len(validation_report.issues_found)}")
        print(f"Performance score: {validation_report.performance_metrics.get('performance_score', 0):.1f}/100")
        
        # Show validation details
        if validation_report.validation_results:
            print("\nValidation Rule Results:")
            for result in validation_report.validation_results:
                status_icon = "✓" if result['status'].value == "pass" else "❌" if result['status'].value == "fail" else "⚠"
                print(f"  {status_icon} {result['rule_name']}: {result['message']}")
        
        print("✓ Validation integration test completed successfully")
        
    except Exception as e:
        print(f"❌ Validation integration test failed: {str(e)}")
    finally:
        db.close()


def main():
    """Main test function."""
    # Test API integration
    test_api_query_validation()
    
    # Test direct validation integration
    asyncio.run(test_validation_integration())


if __name__ == "__main__":
    main()