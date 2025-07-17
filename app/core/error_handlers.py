"""
Comprehensive error handlers for the Quick Commerce Deals API
"""
import logging
import traceback
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from slowapi.errors import RateLimitExceeded

from app.core.exceptions import (
    QuickCommerceException,
    ValidationError,
    QueryProcessingError,
    DatabaseError,
    ProductNotFoundError,
    PlatformNotFoundError,
    RateLimitExceededError,
    InvalidQueryError,
    CacheError,
    ExternalServiceError,
    ConfigurationError,
    AuthenticationError,
    AuthorizationError
)

# Set up logging
logger = logging.getLogger(__name__)


def create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    suggestions: Optional[list] = None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create standardized error response"""
    
    error_response = {
        "error": {
            "code": error_code,
            "message": message,
            "suggestions": suggestions or [],
            "details": details or {},
            "timestamp": None,  # Will be set by middleware
            "request_id": request_id
        }
    }
    
    response = JSONResponse(
        status_code=status_code,
        content=error_response
    )
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response


async def quick_commerce_exception_handler(request: Request, exc: QuickCommerceException) -> JSONResponse:
    """Handler for custom QuickCommerceException and its subclasses"""
    
    # Log the error
    logger.error(
        f"QuickCommerceException: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Determine status code based on error type
    status_code_map = {
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "QUERY_PROCESSING_ERROR": status.HTTP_400_BAD_REQUEST,
        "PRODUCT_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "PLATFORM_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "RATE_LIMIT_EXCEEDED": status.HTTP_429_TOO_MANY_REQUESTS,
        "INVALID_QUERY_ERROR": status.HTTP_400_BAD_REQUEST,
        "DATABASE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "CACHE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "EXTERNAL_SERVICE_ERROR": status.HTTP_502_BAD_GATEWAY,
        "CONFIGURATION_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "AUTHENTICATION_ERROR": status.HTTP_401_UNAUTHORIZED,
        "AUTHORIZATION_ERROR": status.HTTP_403_FORBIDDEN,
        "GENERAL_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR
    }
    
    status_code = status_code_map.get(exc.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return create_error_response(
        status_code=status_code,
        error_code=exc.error_code,
        message=exc.message,
        suggestions=exc.suggestions,
        details=exc.details,
        request_id=getattr(request.state, 'request_id', None)
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler for FastAPI request validation errors"""
    
    # Extract validation error details
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    logger.warning(
        f"Validation error: {len(errors)} field(s) failed validation",
        extra={
            "errors": errors,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        suggestions=[
            "Check required fields and data types",
            "Ensure all parameters meet validation requirements",
            "Review API documentation for correct format"
        ],
        details={"validation_errors": errors},
        request_id=getattr(request.state, 'request_id', None)
    )


async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
    """Handler for Pydantic validation errors"""
    
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        f"Pydantic validation error: {len(errors)} field(s) failed validation",
        extra={
            "errors": errors,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        message="Data validation failed",
        suggestions=[
            "Check data types and formats",
            "Ensure required fields are provided",
            "Review field constraints and limits"
        ],
        details={"validation_errors": errors},
        request_id=getattr(request.state, 'request_id', None)
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handler for SQLAlchemy database errors"""
    
    # Log the full error for debugging
    logger.error(
        f"Database error: {type(exc).__name__} - {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )
    
    # Determine specific error type and message
    if isinstance(exc, IntegrityError):
        error_code = "DATABASE_INTEGRITY_ERROR"
        message = "Data integrity constraint violation"
        suggestions = [
            "Check for duplicate entries",
            "Ensure foreign key references exist",
            "Verify data constraints are met"
        ]
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, OperationalError):
        error_code = "DATABASE_OPERATIONAL_ERROR"
        message = "Database operation failed"
        suggestions = [
            "Try again in a few moments",
            "Check database connectivity",
            "Contact support if the problem persists"
        ]
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    else:
        error_code = "DATABASE_ERROR"
        message = "Database error occurred"
        suggestions = [
            "Try again in a few moments",
            "Contact support if the problem persists"
        ]
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return create_error_response(
        status_code=status_code,
        error_code=error_code,
        message=message,
        suggestions=suggestions,
        details={"error_type": type(exc).__name__},
        request_id=getattr(request.state, 'request_id', None)
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler for FastAPI HTTP exceptions"""
    
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Map HTTP status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE"
    }
    
    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
    
    # Handle different types of detail
    if isinstance(exc.detail, dict):
        message = exc.detail.get("message", str(exc.detail))
        suggestions = exc.detail.get("suggestions", [])
        details = {k: v for k, v in exc.detail.items() if k not in ["message", "suggestions"]}
    else:
        message = str(exc.detail)
        suggestions = []
        details = {}
    
    return create_error_response(
        status_code=exc.status_code,
        error_code=error_code,
        message=message,
        suggestions=suggestions,
        details=details,
        request_id=getattr(request.state, 'request_id', None)
    )


async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Handler for rate limit exceeded errors"""
    
    logger.warning(
        f"Rate limit exceeded: {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    retry_after = getattr(exc, 'retry_after', None)
    
    response = create_error_response(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        error_code="RATE_LIMIT_EXCEEDED",
        message=f"Rate limit exceeded: {exc.detail}",
        suggestions=[
            "Wait before making another request",
            "Reduce request frequency",
            "Consider upgrading your plan for higher limits"
        ],
        details={"retry_after": retry_after},
        request_id=getattr(request.state, 'request_id', None)
    )
    
    if retry_after:
        response.headers["Retry-After"] = str(retry_after)
    
    return response


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for unexpected exceptions"""
    
    # Log the full error with traceback
    logger.error(
        f"Unexpected error: {type(exc).__name__} - {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )
    
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        suggestions=[
            "Try again in a few moments",
            "Contact support if the problem persists"
        ],
        details={"error_type": type(exc).__name__},
        request_id=getattr(request.state, 'request_id', None)
    )


# Dictionary mapping exception types to their handlers
EXCEPTION_HANDLERS = {
    QuickCommerceException: quick_commerce_exception_handler,
    ValidationError: quick_commerce_exception_handler,
    QueryProcessingError: quick_commerce_exception_handler,
    DatabaseError: quick_commerce_exception_handler,
    ProductNotFoundError: quick_commerce_exception_handler,
    PlatformNotFoundError: quick_commerce_exception_handler,
    RateLimitExceededError: quick_commerce_exception_handler,
    InvalidQueryError: quick_commerce_exception_handler,
    CacheError: quick_commerce_exception_handler,
    ExternalServiceError: quick_commerce_exception_handler,
    ConfigurationError: quick_commerce_exception_handler,
    AuthenticationError: quick_commerce_exception_handler,
    AuthorizationError: quick_commerce_exception_handler,
    RequestValidationError: validation_exception_handler,
    PydanticValidationError: pydantic_validation_exception_handler,
    SQLAlchemyError: sqlalchemy_exception_handler,
    HTTPException: http_exception_handler,
    RateLimitExceeded: rate_limit_exception_handler,
    Exception: general_exception_handler
}