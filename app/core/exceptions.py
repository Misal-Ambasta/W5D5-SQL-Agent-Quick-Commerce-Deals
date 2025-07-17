"""
Custom exception classes for the Quick Commerce Deals API
"""
from typing import Optional, List, Dict, Any


class QuickCommerceException(Exception):
    """Base exception class for Quick Commerce Deals API"""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "GENERAL_ERROR",
        suggestions: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.suggestions = suggestions or []
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(QuickCommerceException):
    """Raised when input validation fails"""
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            suggestions=suggestions or [
                "Check input parameters",
                "Ensure all required fields are provided",
                "Verify data types and formats"
            ],
            details={"field": field} if field else {}
        )


class QueryProcessingError(QuickCommerceException):
    """Raised when natural language query cannot be processed"""
    
    def __init__(
        self, 
        message: str, 
        query: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            error_code="QUERY_PROCESSING_ERROR",
            suggestions=suggestions or [
                "Try rephrasing your query",
                "Use more specific product names",
                "Check spelling and grammar",
                "Try simpler query structure"
            ],
            details={"original_query": query} if query else {}
        )


class DatabaseError(QuickCommerceException):
    """Raised when database operations fail"""
    
    def __init__(
        self, 
        message: str, 
        operation: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            suggestions=suggestions or [
                "Try again in a few moments",
                "Check if the service is available",
                "Contact support if the problem persists"
            ],
            details={"operation": operation} if operation else {}
        )


class ProductNotFoundError(QuickCommerceException):
    """Raised when requested product is not found"""
    
    def __init__(
        self, 
        product_name: str,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=f"Product '{product_name}' not found",
            error_code="PRODUCT_NOT_FOUND",
            suggestions=suggestions or [
                "Check product name spelling",
                "Try using more general product terms",
                "Browse available categories",
                "Use partial product names"
            ],
            details={"product_name": product_name}
        )


class PlatformNotFoundError(QuickCommerceException):
    """Raised when requested platform is not found or inactive"""
    
    def __init__(
        self, 
        platform_name: str,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=f"Platform '{platform_name}' not found or inactive",
            error_code="PLATFORM_NOT_FOUND",
            suggestions=suggestions or [
                "Check platform name spelling",
                "Use supported platform names: Blinkit, Zepto, Instamart, BigBasket",
                "Try without specifying platform"
            ],
            details={"platform_name": platform_name}
        )


class RateLimitExceededError(QuickCommerceException):
    """Raised when API rate limits are exceeded"""
    
    def __init__(
        self, 
        limit: str,
        retry_after: Optional[int] = None,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=f"Rate limit exceeded: {limit}",
            error_code="RATE_LIMIT_EXCEEDED",
            suggestions=suggestions or [
                "Wait before making another request",
                "Reduce request frequency",
                "Consider upgrading your plan for higher limits"
            ],
            details={"limit": limit, "retry_after": retry_after}
        )


class InvalidQueryError(QuickCommerceException):
    """Raised when generated SQL query is invalid or unsafe"""
    
    def __init__(
        self, 
        message: str,
        query: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            error_code="INVALID_QUERY_ERROR",
            suggestions=suggestions or [
                "Simplify your query",
                "Use more specific terms",
                "Try breaking complex queries into parts"
            ],
            details={"generated_query": query} if query else {}
        )


class CacheError(QuickCommerceException):
    """Raised when cache operations fail"""
    
    def __init__(
        self, 
        message: str,
        operation: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            suggestions=suggestions or [
                "Request will proceed without cache",
                "Try again if performance is slow"
            ],
            details={"operation": operation} if operation else {}
        )


class ExternalServiceError(QuickCommerceException):
    """Raised when external service calls fail"""
    
    def __init__(
        self, 
        service_name: str,
        message: str,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=f"External service '{service_name}' error: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            suggestions=suggestions or [
                "Try again in a few moments",
                "Check service availability",
                "Contact support if the problem persists"
            ],
            details={"service_name": service_name}
        )


class ConfigurationError(QuickCommerceException):
    """Raised when configuration is invalid or missing"""
    
    def __init__(
        self, 
        message: str,
        config_key: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            suggestions=suggestions or [
                "Check environment variables",
                "Verify configuration files",
                "Contact administrator"
            ],
            details={"config_key": config_key} if config_key else {}
        )


class AuthenticationError(QuickCommerceException):
    """Raised when authentication fails"""
    
    def __init__(
        self, 
        message: str = "Authentication failed",
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            suggestions=suggestions or [
                "Check your API key",
                "Ensure proper authentication headers",
                "Contact support for access issues"
            ]
        )


class AuthorizationError(QuickCommerceException):
    """Raised when authorization fails"""
    
    def __init__(
        self, 
        message: str = "Access denied",
        resource: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            suggestions=suggestions or [
                "Check your permissions",
                "Contact administrator for access",
                "Verify your subscription plan"
            ],
            details={"resource": resource} if resource else {}
        )