"""
Test script to verify error handling implementation
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.exceptions import (
    ValidationError,
    QueryProcessingError,
    DatabaseError,
    ProductNotFoundError,
    PlatformNotFoundError
)
from app.core.validation import InputValidator


def test_custom_exceptions():
    """Test custom exception classes"""
    print("Testing custom exceptions...")
    
    # Test ValidationError
    try:
        raise ValidationError("Test validation error", field="test_field")
    except ValidationError as e:
        print(f"✓ ValidationError: {e.message} (code: {e.error_code})")
        assert e.error_code == "VALIDATION_ERROR"
        assert e.details["field"] == "test_field"
    
    # Test QueryProcessingError
    try:
        raise QueryProcessingError("Test query error", query="test query")
    except QueryProcessingError as e:
        print(f"✓ QueryProcessingError: {e.message} (code: {e.error_code})")
        assert e.error_code == "QUERY_PROCESSING_ERROR"
        assert e.details["original_query"] == "test query"
    
    # Test ProductNotFoundError
    try:
        raise ProductNotFoundError("onions")
    except ProductNotFoundError as e:
        print(f"✓ ProductNotFoundError: {e.message} (code: {e.error_code})")
        assert e.error_code == "PRODUCT_NOT_FOUND"
        assert e.details["product_name"] == "onions"
    
    print("All custom exceptions working correctly!\n")


def test_input_validation():
    """Test input validation utilities"""
    print("Testing input validation...")
    
    # Test valid query string
    try:
        result = InputValidator.validate_query_string("Which app has cheapest onions?")
        print(f"✓ Valid query validated: {result}")
        assert result == "Which app has cheapest onions?"
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    # Test invalid query string (too short)
    try:
        InputValidator.validate_query_string("hi")
        print("✗ Should have failed for short query")
        return False
    except ValidationError as e:
        print(f"✓ Short query rejected: {e.message}")
    
    # Test SQL injection attempt
    try:
        InputValidator.validate_query_string("SELECT * FROM users; DROP TABLE products;")
        print("✗ Should have failed for SQL injection")
        return False
    except ValidationError as e:
        print(f"✓ SQL injection attempt blocked: {e.message}")
    
    # Test valid product name
    try:
        result = InputValidator.validate_product_name("Red Onions (1kg)")
        print(f"✓ Valid product name: {result}")
        assert result == "Red Onions (1kg)"
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    # Test valid platform name
    try:
        result = InputValidator.validate_platform_name("blinkit")
        print(f"✓ Valid platform name: {result}")
        assert result == "Blinkit"
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    # Test invalid platform name
    try:
        InputValidator.validate_platform_name("invalid_platform")
        print("✗ Should have failed for invalid platform")
        return False
    except ValidationError as e:
        print(f"✓ Invalid platform rejected: {e.message}")
    
    # Test discount percentage validation
    try:
        result = InputValidator.validate_discount_percentage(25.5)
        print(f"✓ Valid discount percentage: {result}")
        assert result == 25.5
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    # Test invalid discount percentage
    try:
        InputValidator.validate_discount_percentage(150)
        print("✗ Should have failed for discount > 100%")
        return False
    except ValidationError as e:
        print(f"✓ Invalid discount rejected: {e.message}")
    
    # Test platform list validation
    try:
        result = InputValidator.validate_platform_list("blinkit,zepto,instamart")
        print(f"✓ Valid platform list: {result}")
        assert result == ["Blinkit", "Zepto", "Instamart"]
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    print("All input validation tests passed!\n")
    return True


def test_sanitization():
    """Test input sanitization"""
    print("Testing input sanitization...")
    
    # Test HTML escaping
    try:
        result = InputValidator.sanitize_string("<script>alert('xss')</script>")
        print(f"✓ HTML escaped: {result}")
        assert "&lt;script&gt;" in result
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    # Test XSS pattern detection
    try:
        InputValidator.sanitize_string("javascript:alert('xss')")
        print("✗ Should have failed for XSS pattern")
        return False
    except ValidationError as e:
        print(f"✓ XSS pattern blocked: {e.message}")
    
    # Test user ID sanitization
    try:
        result = InputValidator.sanitize_user_id("user_123-abc")
        print(f"✓ Valid user ID: {result}")
        assert result == "user_123-abc"
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    # Test invalid user ID
    try:
        InputValidator.sanitize_user_id("user@123.com")
        print("✗ Should have failed for invalid user ID")
        return False
    except ValidationError as e:
        print(f"✓ Invalid user ID rejected: {e.message}")
    
    print("All sanitization tests passed!\n")
    return True


def main():
    """Run all tests"""
    print("=== Error Handling Implementation Test ===\n")
    
    try:
        test_custom_exceptions()
        
        if not test_input_validation():
            print("Input validation tests failed!")
            return False
        
        if not test_sanitization():
            print("Sanitization tests failed!")
            return False
        
        print("🎉 All error handling tests passed successfully!")
        print("\nImplemented features:")
        print("✓ Custom exception classes with error codes and suggestions")
        print("✓ Comprehensive input validation and sanitization")
        print("✓ SQL injection prevention")
        print("✓ XSS protection")
        print("✓ Platform and product name validation")
        print("✓ Discount percentage validation")
        print("✓ Query string validation")
        print("✓ User ID sanitization")
        
        return True
        
    except Exception as e:
        print(f"Test failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)