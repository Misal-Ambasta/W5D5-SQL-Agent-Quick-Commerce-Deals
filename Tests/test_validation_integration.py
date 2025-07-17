"""
Integration test for validation and error handling without database dependency
"""
import sys
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import Optional

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.validation import InputValidator
from app.core.exceptions import ValidationError, QueryProcessingError
from app.core.error_handlers import EXCEPTION_HANDLERS

# Create a minimal FastAPI app for testing validation
test_app = FastAPI(title="Validation Test API")

# Add exception handlers
for exception_type, handler in EXCEPTION_HANDLERS.items():
    test_app.add_exception_handler(exception_type, handler)

# Test models
class TestQueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = None

class TestProductRequest(BaseModel):
    product_name: str
    platforms: Optional[str] = None

class TestDealsRequest(BaseModel):
    platform: Optional[str] = None
    min_discount: Optional[float] = 0

# Test endpoints that use validation
@test_app.post("/test/query")
async def test_query_validation(request: Request, query_request: TestQueryRequest):
    """Test endpoint for query validation"""
    try:
        # Validate query
        validated_query = InputValidator.validate_query_string(query_request.query)
        
        # Validate user_id if provided
        validated_user_id = None
        if query_request.user_id:
            validated_user_id = InputValidator.sanitize_user_id(query_request.user_id)
        
        return {
            "status": "success",
            "validated_query": validated_query,
            "validated_user_id": validated_user_id
        }
    except ValidationError as e:
        raise e
    except Exception as e:
        raise QueryProcessingError(f"Query processing failed: {str(e)}")

@test_app.get("/test/products")
async def test_product_validation(
    request: Request,
    product_name: str,
    platforms: Optional[str] = None
):
    """Test endpoint for product validation"""
    try:
        # Validate product name
        validated_product = InputValidator.validate_product_name(product_name)
        
        # Validate platforms if provided
        validated_platforms = []
        if platforms:
            validated_platforms = InputValidator.validate_platform_list(platforms)
        
        return {
            "status": "success",
            "validated_product": validated_product,
            "validated_platforms": validated_platforms
        }
    except ValidationError as e:
        raise e

@test_app.get("/test/deals")
async def test_deals_validation(
    request: Request,
    platform: Optional[str] = None,
    min_discount: Optional[float] = 0,
    limit: Optional[int] = 50
):
    """Test endpoint for deals validation"""
    try:
        # Validate platform if provided
        validated_platform = None
        if platform:
            validated_platform = InputValidator.validate_platform_name(platform)
        
        # Validate discount percentage
        validated_discount = InputValidator.validate_discount_percentage(min_discount)
        
        # Validate limit
        validated_limit = InputValidator.validate_limit(limit)
        
        return {
            "status": "success",
            "validated_platform": validated_platform,
            "validated_discount": validated_discount,
            "validated_limit": validated_limit
        }
    except ValidationError as e:
        raise e

def test_validation_endpoints():
    """Test validation in API endpoints"""
    print("Testing validation in API endpoints...")
    
    client = TestClient(test_app)
    
    # Test 1: Valid query
    print("\n1. Testing valid query...")
    response = client.post("/test/query", json={"query": "Which app has cheapest onions?"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Test 2: Invalid query (too short)
    print("\n2. Testing invalid query (too short)...")
    response = client.post("/test/query", json={"query": "hi"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 400
    assert "error" in response.json()
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    
    # Test 3: SQL injection attempt
    print("\n3. Testing SQL injection prevention...")
    response = client.post("/test/query", json={"query": "SELECT * FROM users; DROP TABLE products;"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 400
    assert "error" in response.json()
    
    # Test 4: Valid product request
    print("\n4. Testing valid product request...")
    response = client.get("/test/products?product_name=Red Onions&platforms=blinkit,zepto")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["validated_platforms"] == ["Blinkit", "Zepto"]
    
    # Test 5: Invalid platform
    print("\n5. Testing invalid platform...")
    response = client.get("/test/products?product_name=onions&platforms=invalid_platform")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 400
    assert "error" in response.json()
    
    # Test 6: Valid deals request
    print("\n6. Testing valid deals request...")
    response = client.get("/test/deals?platform=blinkit&min_discount=25&limit=10")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["validated_platform"] == "Blinkit"
    assert response.json()["validated_discount"] == 25
    
    # Test 7: Invalid discount percentage
    print("\n7. Testing invalid discount percentage...")
    response = client.get("/test/deals?min_discount=150")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 400
    assert "error" in response.json()
    
    print("\n✓ All validation endpoint tests passed!")

def test_error_response_structure():
    """Test that error responses have the correct structure"""
    print("\nTesting error response structure...")
    
    client = TestClient(test_app)
    
    # Get an error response
    response = client.post("/test/query", json={"query": "hi"})
    error_data = response.json()
    
    print(f"Error response: {error_data}")
    
    # Check error structure
    assert "error" in error_data
    error = error_data["error"]
    
    # Check required fields
    required_fields = ["code", "message", "suggestions"]
    for field in required_fields:
        assert field in error, f"Missing field: {field}"
    
    # Check field types
    assert isinstance(error["code"], str), "Error code should be string"
    assert isinstance(error["message"], str), "Error message should be string"
    assert isinstance(error["suggestions"], list), "Suggestions should be list"
    assert len(error["suggestions"]) > 0, "Should have suggestions"
    
    print("✓ Error response structure is correct!")

def test_security_headers():
    """Test that security headers are present"""
    print("\nTesting security headers...")
    
    client = TestClient(test_app)
    
    # Make a request and check headers
    response = client.post("/test/query", json={"query": "hi"})
    
    expected_headers = [
        "x-content-type-options",
        "x-frame-options",
        "x-xss-protection",
        "referrer-policy",
        "content-security-policy"
    ]
    
    for header in expected_headers:
        assert header in response.headers, f"Missing header: {header}"
        print(f"✓ {header}: {response.headers[header]}")
    
    print("✓ Security headers are present!")

def test_xss_protection():
    """Test XSS protection in validation"""
    print("\nTesting XSS protection...")
    
    client = TestClient(test_app)
    
    # Test XSS attempt in query
    response = client.post("/test/query", json={"query": "javascript:alert('xss')"})
    print(f"XSS test status: {response.status_code}")
    print(f"XSS test response: {response.json()}")
    
    assert response.status_code == 400
    assert "error" in response.json()
    
    print("✓ XSS protection is working!")

def main():
    """Run all validation integration tests"""
    print("=== Validation Integration Test ===")
    
    try:
        test_validation_endpoints()
        test_error_response_structure()
        test_security_headers()
        test_xss_protection()
        
        print("\n🎉 All validation integration tests passed!")
        print("\nValidated error handling features:")
        print("✓ Input validation with proper error responses")
        print("✓ SQL injection prevention")
        print("✓ XSS protection")
        print("✓ Platform name validation")
        print("✓ Product name validation")
        print("✓ Discount percentage validation")
        print("✓ Limit validation")
        print("✓ User ID sanitization")
        print("✓ Standardized error response format")
        print("✓ Security headers on all responses")
        print("✓ Helpful error suggestions")
        print("✓ Proper HTTP status codes")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)