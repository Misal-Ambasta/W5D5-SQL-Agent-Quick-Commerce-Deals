# FastAPI Application Structure

This document describes the FastAPI application structure and configuration for the Quick Commerce Deals platform.

## Features Implemented

### 1. Rate Limiting with SlowAPI
- **Implementation**: Using `slowapi` library with IP-based rate limiting
- **Configuration**: Configurable rate limits via environment variables
- **Default**: 60 requests per minute per IP address
- **Error Handling**: Custom rate limit exceeded handler with proper HTTP 429 responses

### 2. Security Headers Middleware
- **X-Content-Type-Options**: `nosniff`
- **X-Frame-Options**: `DENY`
- **X-XSS-Protection**: `1; mode=block`
- **Referrer-Policy**: `strict-origin-when-cross-origin`
- **Content-Security-Policy**: `default-src 'self'`
- **Strict-Transport-Security**: `max-age=31536000; includeSubDomains`
- **Permissions-Policy**: `geolocation=(), microphone=(), camera=()`

### 3. Database Connection Pooling
- **Engine**: SQLAlchemy with PostgreSQL
- **Pool Configuration**: 
  - Pool size: 10 connections
  - Max overflow: 20 connections
  - Pre-ping enabled for connection health checks
- **Session Management**: Proper session lifecycle with error handling

### 4. CORS Middleware
- **Allowed Origins**: Configurable via environment variables
- **Default Origins**: localhost:3000, localhost:8000, localhost:8501
- **Credentials**: Enabled
- **Methods**: All methods allowed
- **Headers**: All headers allowed

### 5. Custom Middleware

#### SecurityHeadersMiddleware
- Adds comprehensive security headers to all responses
- Implements security best practices

#### RequestLoggingMiddleware
- Logs all incoming requests with timing information
- Includes client IP, method, path, status code, and processing time
- Adds `X-Process-Time` header to responses

#### DatabaseHealthMiddleware
- Monitors database connectivity for critical endpoints
- Returns HTTP 503 if database is unavailable for critical paths
- Critical paths: `/api/v1/query`, `/api/v1/products`, `/api/v1/deals`

## Application Structure

```
app/
├── main.py                 # FastAPI application entry point
├── core/
│   ├── config.py          # Configuration management
│   ├── database.py        # Database connection and session management
│   ├── dependencies.py    # FastAPI dependencies
│   ├── middleware.py      # Custom middleware classes
│   └── logging.py         # Logging configuration
└── api/
    └── v1/
        ├── api.py         # API router configuration
        └── endpoints/     # API endpoint implementations
```

## Configuration

### Environment Variables
- `RATE_LIMIT_PER_MINUTE`: Rate limit per IP (default: 60)
- `DB_POOL_SIZE`: Database connection pool size (default: 10)
- `DB_MAX_OVERFLOW`: Max overflow connections (default: 20)
- `BACKEND_CORS_ORIGINS`: Allowed CORS origins
- `POSTGRES_*`: Database connection parameters

### Health Check Endpoint
- **URL**: `/health`
- **Method**: GET
- **Response**: JSON with application status and database connectivity
- **Rate Limited**: Yes

## Error Handling

### Rate Limiting Errors
- **Status Code**: 429 Too Many Requests
- **Response**: JSON with error details and retry information
- **Headers**: Security headers included

### Database Errors
- **Status Code**: 503 Service Unavailable (for critical endpoints)
- **Response**: JSON with service unavailable message
- **Fallback**: Graceful degradation for non-critical endpoints

## Testing

Run the test script to verify all features:

```bash
python test_fastapi_setup.py
```

This will test:
- Basic endpoint functionality
- Security headers presence
- Database connection handling
- Rate limiting configuration
- CORS setup
- Middleware functionality

## Usage

### Starting the Application

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## Security Considerations

1. **Rate Limiting**: Prevents abuse and DoS attacks
2. **Security Headers**: Protects against common web vulnerabilities
3. **CORS Configuration**: Restricts cross-origin requests to allowed domains
4. **Database Health Checks**: Ensures service availability
5. **Request Logging**: Enables monitoring and debugging
6. **Error Handling**: Prevents information leakage

## Performance Features

1. **Connection Pooling**: Efficient database connection management
2. **Request Timing**: Performance monitoring with response headers
3. **Health Checks**: Proactive service monitoring
4. **Caching Ready**: Structure supports Redis integration
5. **Async Support**: Full async/await support throughout

This FastAPI setup provides a robust, secure, and scalable foundation for the Quick Commerce Deals platform.