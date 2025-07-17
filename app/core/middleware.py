"""
Custom middleware for the FastAPI application
"""
import time
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced middleware to log all requests with comprehensive monitoring integration
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log request start
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "event_type": "request_start",
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
                "user_agent": user_agent
            }
        )
        
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log request completion with comprehensive data
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "event_type": "request_complete",
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": round(process_time, 4),
                "client_ip": client_ip,
                "user_agent": user_agent,
                "response_size": response.headers.get("content-length", "unknown")
            }
        )
        
        # Integrate with API usage monitoring
        try:
            from app.core.logging import api_usage_logger
            api_usage_logger.log_api_request(
                endpoint=request.url.path,
                method=request.method,
                client_ip=client_ip,
                response_time=process_time,
                status_code=response.status_code,
                user_agent=user_agent
            )
        except Exception as e:
            logger.warning(f"Failed to log API usage: {e}")
        
        # Add comprehensive response headers
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        response.headers["X-Request-ID"] = f"{int(start_time * 1000)}-{hash(client_ip) % 10000}"
        
        return response


class DatabaseHealthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check database health on critical endpoints
    """
    
    def __init__(self, app, critical_paths: list = None):
        super().__init__(app)
        self.critical_paths = critical_paths or ["/api/v1/query", "/api/v1/products", "/api/v1/deals"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if this is a critical path that requires database
        if any(request.url.path.startswith(path) for path in self.critical_paths):
            try:
                from app.core.database import SessionLocal
                from sqlalchemy import text
                # Quick database health check
                db = SessionLocal()
                db.execute(text("SELECT 1"))
                db.close()
            except Exception as e:
                logger.error(f"Database health check failed for {request.url.path}: {e}")
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "Service Unavailable",
                        "message": "Database connection is currently unavailable",
                        "path": request.url.path
                    }
                )
        
        return await call_next(request)