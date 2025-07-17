"""
Input validation and sanitization utilities
"""
import re
import html
import logging
from typing import Optional, List, Dict, Any, Union
from urllib.parse import quote, unquote

from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class InputValidator:
    """Comprehensive input validation and sanitization"""
    
    # SQL injection patterns to detect and block
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|SCRIPT)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
        r"(;|\|\||&&)",
        r"(\bxp_cmdshell\b|\bsp_executesql\b)",
        r"(\b(INFORMATION_SCHEMA|SYSOBJECTS|SYSCOLUMNS)\b)"
    ]
    
    # XSS patterns to detect and sanitize
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>.*?</embed>"
    ]
    
    @staticmethod
    def sanitize_string(
        value: str, 
        max_length: Optional[int] = None,
        allow_html: bool = False,
        strip_whitespace: bool = True
    ) -> str:
        """Sanitize string input"""
        
        if not isinstance(value, str):
            raise ValidationError(f"Expected string, got {type(value).__name__}")
        
        # Strip whitespace if requested
        if strip_whitespace:
            value = value.strip()
        
        # Check length
        if max_length and len(value) > max_length:
            raise ValidationError(f"String too long. Maximum length: {max_length}")
        
        # HTML escape if HTML is not allowed
        if not allow_html:
            value = html.escape(value)
        
        # Check for XSS patterns
        for pattern in InputValidator.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential XSS attempt detected: {pattern}")
                raise ValidationError("Invalid characters detected in input")
        
        return value
    
    @staticmethod
    def validate_query_string(query: str) -> str:
        """Validate and sanitize natural language query string"""
        
        if not query or not isinstance(query, str):
            raise ValidationError("Query must be a non-empty string")
        
        # Basic length validation
        query = query.strip()
        if len(query) < 3:
            raise ValidationError("Query too short. Minimum 3 characters required")
        
        if len(query) > 500:
            raise ValidationError("Query too long. Maximum 500 characters allowed")
        
        # Check for SQL injection patterns
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                logger.warning(f"Potential SQL injection attempt detected: {pattern}")
                raise ValidationError("Invalid query format detected")
        
        # Sanitize the query
        query = InputValidator.sanitize_string(query, max_length=500, allow_html=False)
        
        return query
    
    @staticmethod
    def validate_product_name(product_name: str) -> str:
        """Validate product name input"""
        
        if not product_name or not isinstance(product_name, str):
            raise ValidationError("Product name must be a non-empty string")
        
        product_name = product_name.strip()
        
        if len(product_name) < 1:
            raise ValidationError("Product name cannot be empty")
        
        if len(product_name) > 200:
            raise ValidationError("Product name too long. Maximum 200 characters allowed")
        
        # Allow alphanumeric, spaces, hyphens, parentheses, and common punctuation
        if not re.match(r"^[a-zA-Z0-9\s\-\(\)\.\,\&\%\/]+$", product_name):
            raise ValidationError("Product name contains invalid characters")
        
        return InputValidator.sanitize_string(product_name, max_length=200)
    
    @staticmethod
    def validate_platform_name(platform_name: str) -> str:
        """Validate platform name input"""
        
        if not platform_name or not isinstance(platform_name, str):
            raise ValidationError("Platform name must be a non-empty string")
        
        platform_name = platform_name.strip()
        
        # List of valid platforms
        valid_platforms = [
            "blinkit", "zepto", "instamart", "bigbasket", "swiggy", 
            "dunzo", "grofers", "amazon", "flipkart"
        ]
        
        if platform_name.lower() not in valid_platforms:
            raise ValidationError(
                f"Invalid platform name. Supported platforms: {', '.join(valid_platforms)}"
            )
        
        return platform_name.title()  # Return with proper capitalization
    
    @staticmethod
    def validate_category_name(category_name: str) -> str:
        """Validate category name input"""
        
        if not category_name or not isinstance(category_name, str):
            raise ValidationError("Category name must be a non-empty string")
        
        category_name = category_name.strip()
        
        if len(category_name) > 100:
            raise ValidationError("Category name too long. Maximum 100 characters allowed")
        
        # Allow alphanumeric, spaces, hyphens, and ampersands
        if not re.match(r"^[a-zA-Z0-9\s\-\&]+$", category_name):
            raise ValidationError("Category name contains invalid characters")
        
        return InputValidator.sanitize_string(category_name, max_length=100)
    
    @staticmethod
    def validate_discount_percentage(discount: Union[int, float]) -> float:
        """Validate discount percentage"""
        
        try:
            discount = float(discount)
        except (ValueError, TypeError):
            raise ValidationError("Discount percentage must be a number")
        
        if discount < 0:
            raise ValidationError("Discount percentage cannot be negative")
        
        if discount > 100:
            raise ValidationError("Discount percentage cannot exceed 100%")
        
        return discount
    
    @staticmethod
    def validate_limit(limit: Union[int, str]) -> int:
        """Validate limit parameter"""
        
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            raise ValidationError("Limit must be a valid integer")
        
        if limit < 1:
            raise ValidationError("Limit must be at least 1")
        
        if limit > 1000:
            raise ValidationError("Limit cannot exceed 1000")
        
        return limit
    
    @staticmethod
    def validate_platform_list(platforms: Union[str, List[str]]) -> List[str]:
        """Validate list of platform names"""
        
        if isinstance(platforms, str):
            # Split comma-separated string
            platform_list = [p.strip() for p in platforms.split(',') if p.strip()]
        elif isinstance(platforms, list):
            platform_list = [str(p).strip() for p in platforms if str(p).strip()]
        else:
            raise ValidationError("Platforms must be a string or list of strings")
        
        if not platform_list:
            raise ValidationError("At least one platform must be specified")
        
        if len(platform_list) > 10:
            raise ValidationError("Too many platforms specified. Maximum 10 allowed")
        
        # Validate each platform
        validated_platforms = []
        for platform in platform_list:
            validated_platforms.append(InputValidator.validate_platform_name(platform))
        
        return validated_platforms
    
    @staticmethod
    def sanitize_user_id(user_id: Optional[str]) -> Optional[str]:
        """Sanitize user ID"""
        
        if not user_id:
            return None
        
        if not isinstance(user_id, str):
            raise ValidationError("User ID must be a string")
        
        user_id = user_id.strip()
        
        if len(user_id) > 100:
            raise ValidationError("User ID too long. Maximum 100 characters allowed")
        
        # Allow alphanumeric, hyphens, and underscores
        if not re.match(r"^[a-zA-Z0-9\-_]+$", user_id):
            raise ValidationError("User ID contains invalid characters")
        
        return user_id
    
    @staticmethod
    def validate_context_data(context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate context data"""
        
        if context is None:
            return None
        
        if not isinstance(context, dict):
            raise ValidationError("Context must be a dictionary")
        
        # Limit context size
        if len(str(context)) > 1000:
            raise ValidationError("Context data too large. Maximum 1000 characters allowed")
        
        # Validate context keys and values
        validated_context = {}
        for key, value in context.items():
            if not isinstance(key, str):
                raise ValidationError("Context keys must be strings")
            
            if len(key) > 50:
                raise ValidationError("Context key too long. Maximum 50 characters allowed")
            
            # Sanitize string values
            if isinstance(value, str):
                value = InputValidator.sanitize_string(value, max_length=200)
            elif isinstance(value, (int, float, bool)):
                pass  # These types are safe
            else:
                raise ValidationError(f"Unsupported context value type: {type(value).__name__}")
            
            validated_context[key] = value
        
        return validated_context
    
    @staticmethod
    def validate_price_range(min_price: Optional[float], max_price: Optional[float]) -> tuple:
        """Validate price range parameters"""
        
        if min_price is not None:
            try:
                min_price = float(min_price)
            except (ValueError, TypeError):
                raise ValidationError("Minimum price must be a number")
            
            if min_price < 0:
                raise ValidationError("Minimum price cannot be negative")
        
        if max_price is not None:
            try:
                max_price = float(max_price)
            except (ValueError, TypeError):
                raise ValidationError("Maximum price must be a number")
            
            if max_price < 0:
                raise ValidationError("Maximum price cannot be negative")
        
        if min_price is not None and max_price is not None:
            if min_price > max_price:
                raise ValidationError("Minimum price cannot be greater than maximum price")
        
        return min_price, max_price
    
    @staticmethod
    def sanitize_url_parameter(param: str) -> str:
        """Sanitize URL parameter"""
        
        if not isinstance(param, str):
            raise ValidationError("URL parameter must be a string")
        
        # URL decode first
        param = unquote(param)
        
        # Sanitize
        param = InputValidator.sanitize_string(param, max_length=200)
        
        # URL encode for safety
        return quote(param, safe='')


class RequestValidator:
    """Request-level validation utilities"""
    
    @staticmethod
    def validate_content_type(request, expected_types: List[str]):
        """Validate request content type"""
        
        content_type = request.headers.get("content-type", "").lower()
        
        if not any(expected_type in content_type for expected_type in expected_types):
            raise ValidationError(
                f"Invalid content type. Expected one of: {', '.join(expected_types)}"
            )
    
    @staticmethod
    def validate_request_size(request, max_size: int = 1024 * 1024):  # 1MB default
        """Validate request body size"""
        
        content_length = request.headers.get("content-length")
        
        if content_length:
            try:
                size = int(content_length)
                if size > max_size:
                    raise ValidationError(f"Request too large. Maximum size: {max_size} bytes")
            except ValueError:
                raise ValidationError("Invalid content-length header")
    
    @staticmethod
    def validate_user_agent(request):
        """Validate user agent header"""
        
        user_agent = request.headers.get("user-agent", "")
        
        # Block suspicious user agents
        suspicious_patterns = [
            r"bot", r"crawler", r"spider", r"scraper", 
            r"curl", r"wget", r"python-requests"
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, user_agent, re.IGNORECASE):
                logger.warning(f"Suspicious user agent detected: {user_agent}")
                # Don't block, just log for now
                break