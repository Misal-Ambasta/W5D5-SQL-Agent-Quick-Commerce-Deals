"""
Error handling middleware for request tracking and response formatting
"""
import uuid
import time
import json
import logging
from datetime import datetime
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for error handling, request tracking, and response formatting"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Record start time
        start_time = time.time()
        
        # Log incoming request
        logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Add custom headers to successful responses
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Processing-Time"] = f"{processing_time:.3f}s"
            
            # Log successful response
            logger.info(
                f"Request completed: {response.status_code}",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "processing_time": processing_time
                }
            )
            
            return response
            
        except Exception as exc:
            # Calculate processing time for errors too
            processing_time = time.time() - start_time
            
            # Log the error
            logger.error(
                f"Request failed: {type(exc).__name__} - {str(exc)}",
                extra={
                    "request_id": request_id,
                    "error_type": type(exc).__name__,
                    "processing_time": processing_time
                }
            )
            
            # Re-raise the exception to be handled by FastAPI's exception handlers
            raise exc


class ResponseFormattingMiddleware(BaseHTTPMiddleware):
    """Middleware to format error responses with timestamps and request IDs"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Only modify JSON error responses
        if (isinstance(response, JSONResponse) and 
            response.status_code >= 400 and 
            hasattr(response, 'body')):
            
            try:
                # Parse the response body
                body = json.loads(response.body.decode())
                
                # Add timestamp and request ID if it's an error response
                if "error" in body:
                    body["error"]["timestamp"] = datetime.utcnow().isoformat() + "Z"
                    body["error"]["request_id"] = getattr(request.state, 'request_id', None)
                    
                    # Create new response with updated body
                    new_response = JSONResponse(
                        content=body,
                        status_code=response.status_code,
                        headers=dict(response.headers)
                    )
                    
                    return new_response
                    
            except (json.JSONDecodeError, AttributeError, KeyError):
                # If we can't parse or modify the response, return it as-is
                pass
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for basic request validation"""
    
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.MAX_REQUEST_SIZE:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": {
                                "code": "REQUEST_TOO_LARGE",
                                "message": f"Request body too large. Maximum size: {self.MAX_REQUEST_SIZE} bytes",
                                "suggestions": [
                                    "Reduce the size of your request",
                                    "Split large requests into smaller ones"
                                ],
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "request_id": getattr(request.state, 'request_id', None)
                            }
                        }
                    )
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "INVALID_CONTENT_LENGTH",
                            "message": "Invalid Content-Length header",
                            "suggestions": [
                                "Check your request headers",
                                "Ensure Content-Length is a valid number"
                            ],
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "request_id": getattr(request.state, 'request_id', None)
                        }
                    }
                )
        
        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "").lower()
            
            # Allow JSON and form data
            allowed_types = ["application/json", "application/x-www-form-urlencoded", "multipart/form-data"]
            
            if not any(allowed_type in content_type for allowed_type in allowed_types):
                return JSONResponse(
                    status_code=415,
                    content={
                        "error": {
                            "code": "UNSUPPORTED_MEDIA_TYPE",
                            "message": f"Unsupported content type: {content_type}",
                            "suggestions": [
                                "Use application/json for JSON requests",
                                "Use application/x-www-form-urlencoded for form data",
                                "Check your Content-Type header"
                            ],
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "request_id": getattr(request.state, 'request_id', None)
                        }
                    }
                )
        
        return await call_next(request)