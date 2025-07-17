"""
FastAPI main application for Quick Commerce Deals platform
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import SQLAlchemyError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.core.database import engine, SessionLocal
from app.core.middleware import SecurityHeadersMiddleware, RequestLoggingMiddleware, DatabaseHealthMiddleware
from app.core.error_handlers import EXCEPTION_HANDLERS
from app.core.error_middleware import (
    ErrorHandlingMiddleware, 
    ResponseFormattingMiddleware, 
    RequestValidationMiddleware
)
from app.core.openapi import setup_openapi_docs
from app.api.v1.api import api_router

# Configure logging
configure_logging()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Quick Commerce Deals API",
    description="Price comparison platform for quick commerce apps",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up rate limiter state
app.state.limiter = limiter

# Add comprehensive exception handlers
for exception_type, handler in EXCEPTION_HANDLERS.items():
    app.add_exception_handler(exception_type, handler)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Add SlowAPI middleware for rate limiting
app.add_middleware(SlowAPIMiddleware)

# Add error handling middleware (order matters - these should be early in the chain)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(ResponseFormattingMiddleware)
app.add_middleware(RequestValidationMiddleware)

# Add custom middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(DatabaseHealthMiddleware)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Setup enhanced OpenAPI documentation
setup_openapi_docs(app)

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Starting Quick Commerce Deals API", version="1.0.0")
    
    # Test database connection
    try:
        from sqlalchemy import text
        # Create a test connection to verify database connectivity
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Database connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
    
    # Initialize monitoring systems
    try:
        from app.core.startup import initialize_monitoring
        await initialize_monitoring()
        logger.info("Monitoring systems initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize monitoring: {e}")
        # Don't fail startup if monitoring fails
    
    logger.info(f"Rate limiting configured: {settings.RATE_LIMIT_PER_MINUTE} requests per minute")
    logger.info(f"Database pool size: {settings.DB_POOL_SIZE}, max overflow: {settings.DB_MAX_OVERFLOW}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down Quick Commerce Deals API")
    
    # Shutdown monitoring systems
    try:
        from app.core.startup import shutdown_monitoring
        await shutdown_monitoring()
        logger.info("Monitoring systems shutdown completed")
    except Exception as e:
        logger.error(f"Error shutting down monitoring: {e}")
    
    # Close database connections
    try:
        engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

@app.get("/")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def root(request: Request):
    return {"message": "Quick Commerce Deals API", "version": "1.0.0"}

@app.get("/health")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def health_check(request: Request):
    """Health check endpoint with database connectivity test"""
    from datetime import datetime
    from sqlalchemy import text
    
    try:
        # Test database connection
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "connected"
        logger.info("Health check completed - database connection successful")
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "version": "1.0.0",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }