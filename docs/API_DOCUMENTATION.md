# Quick Commerce Deals API Documentation

## Overview

The Quick Commerce Deals API is a comprehensive price comparison platform that enables users to query product pricing, discounts, and availability across multiple quick commerce platforms (Blinkit, Zepto, Instamart, BigBasket Now, etc.) using natural language queries.

## Base URL

```
http://localhost:8000
```

## API Version

Current API version: `v1`

All API endpoints are prefixed with `/api/v1`

## Authentication

Currently, the API does not require authentication. Rate limiting is applied based on IP address.

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Natural Language Queries**: 10 requests per minute
- **Advanced Queries**: 5 requests per minute  
- **Product Comparisons**: 20 requests per minute
- **Deals Endpoints**: 30 requests per minute
- **Monitoring Endpoints**: Various limits per endpoint

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when rate limit resets

## Response Format

All API responses follow a consistent JSON structure:

### Success Response
```json
{
  "query": "user query string",
  "results": [...],
  "execution_time": 0.45,
  "total_results": 25,
  "cached": false
}
```

### Error Response
```json
{
  "error": "Error Type",
  "message": "Detailed error message",
  "suggestions": ["suggestion1", "suggestion2"],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Core Endpoints

### 1. Natural Language Query Processing

#### POST `/api/v1/query/`

Process natural language queries and return relevant product pricing information.

**Rate Limit**: 10 requests per minute

**Request Body**:
```json
{
  "query": "Which app has cheapest onions right now?",
  "user_id": "optional_user_id",
  "context": {
    "location": "optional_location",
    "preferences": {}
  }
}
```

**Response**:
```json
{
  "query": "Which app has cheapest onions right now?",
  "results": [
    {
      "product_id": 123,
      "product_name": "Fresh Onions (1kg)",
      "platform_name": "Blinkit",
      "current_price": 45.00,
      "original_price": 50.00,
      "discount_percentage": 10.0,
      "is_available": true,
      "last_updated": "2024-01-15T10:30:00Z"
    }
  ],
  "execution_time": 0.45,
  "relevant_tables": ["products", "current_prices", "platforms"],
  "total_results": 5,
  "cached": false,
  "suggestions": null
}
```

**Sample Queries**:
- "Which app has cheapest onions right now?"
- "Show products with 30%+ discount on Blinkit"
- "Compare fruit prices between Zepto and Instamart"
- "Find best deals for ₹1000 grocery list"

#### POST `/api/v1/query/advanced`

Advanced natural language query processing with configurable pagination, sampling, and formatting.

**Rate Limit**: 5 requests per minute

**Query Parameters**:
- `page` (int): Page number (default: 1)
- `page_size` (int): Results per page (1-100, default: 20)
- `sampling_method` (string): Sampling method - "random", "systematic", "stratified", "top_n", "none" (default: "none")
- `sample_size` (int): Maximum sample size (10-10000, default: 1000)
- `result_format` (string): Result format - "raw", "structured", "summary", "comparison", "chart_data" (default: "structured")

**Request Body**: Same as basic query endpoint

**Response**: Enhanced response with additional metadata for special formats

### 2. Product Comparison

#### GET `/api/v1/products/compare`

Compare product prices across platforms using query parameters.

**Rate Limit**: 20 requests per minute

**Query Parameters**:
- `product_name` (required): Product name to search for
- `platforms`: Comma-separated platform names
- `category`: Product category filter
- `brand`: Brand filter

**Response**:
```json
{
  "query": "onions",
  "comparisons": [
    {
      "product": {
        "id": 123,
        "name": "Fresh Onions (1kg)",
        "brand": "Farm Fresh",
        "category": "Vegetables",
        "description": "Fresh red onions",
        "pack_size": "1kg",
        "is_organic": false
      },
      "platforms": [
        {
          "platform_id": 1,
          "platform_name": "Blinkit",
          "current_price": 45.00,
          "original_price": 50.00,
          "discount_percentage": 10.0,
          "is_available": true,
          "stock_status": "in_stock",
          "delivery_time_minutes": 15,
          "last_updated": "2024-01-15T10:30:00Z"
        }
      ],
      "best_deal": {
        "platform_name": "Blinkit",
        "current_price": 45.00,
        "savings": 5.00
      },
      "savings_potential": 15.00,
      "price_range": {
        "min": 45.00,
        "max": 60.00
      }
    }
  ],
  "total_products": 1,
  "platforms_compared": ["Blinkit", "Zepto", "Instamart"],
  "execution_time": 0.32
}
```

#### POST `/api/v1/products/compare`

Compare products using JSON request body for more complex filtering.

**Request Body**:
```json
{
  "product_name": "onions",
  "platforms": ["Blinkit", "Zepto"],
  "category": "Vegetables",
  "brand": "Farm Fresh"
}
```

### 3. Deals and Discounts

#### GET `/api/v1/deals/`

Get current deals and discounts with filtering options.

**Rate Limit**: 30 requests per minute

**Query Parameters**:
- `platform`: Filter by platform name
- `category`: Filter by product category
- `min_discount`: Minimum discount percentage (0-100)
- `max_discount`: Maximum discount percentage (0-100)
- `featured_only`: Show only featured deals (boolean)
- `active_only`: Show only currently active deals (boolean, default: true)
- `limit`: Maximum number of deals (1-100, default: 50)

**Response**:
```json
{
  "deals": [
    {
      "id": 456,
      "title": "30% Off on Fresh Vegetables",
      "description": "Get 30% discount on all fresh vegetables",
      "discount_type": "percentage",
      "discount_value": 30.0,
      "discount_percentage": 30.0,
      "max_discount_amount": 100.0,
      "min_order_amount": 200.0,
      "discount_code": "FRESH30",
      "platform_name": "Blinkit",
      "product_name": null,
      "category_name": "Vegetables",
      "original_price": 50.0,
      "discounted_price": 35.0,
      "savings_amount": 15.0,
      "is_featured": true,
      "start_date": "2024-01-15T00:00:00Z",
      "end_date": "2024-01-20T23:59:59Z",
      "usage_limit_per_user": 5
    }
  ],
  "total_deals": 1,
  "filters_applied": {
    "platform": null,
    "category": null,
    "min_discount": 0,
    "max_discount": null,
    "featured_only": false,
    "active_only": true,
    "limit": 50
  },
  "platforms_included": ["Blinkit"],
  "categories_included": ["Vegetables"],
  "execution_time": 0.28
}
```

#### POST `/api/v1/deals/`

Get deals using JSON request body for complex filtering.

#### GET `/api/v1/deals/campaigns`

Get promotional campaigns across platforms.

**Query Parameters**:
- `platform`: Filter by platform name
- `campaign_type`: Filter by campaign type
- `featured_only`: Show only featured campaigns (boolean)
- `active_only`: Show only currently active campaigns (boolean, default: true)
- `limit`: Maximum number of campaigns (1-50, default: 20)

### 4. Monitoring and Health

#### GET `/api/v1/monitoring/health`

Comprehensive system health check.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "components": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful"
    },
    "cache": {
      "status": "healthy", 
      "message": "Cache system operational"
    },
    "system": {
      "status": "healthy",
      "message": "System resources normal"
    }
  }
}
```

#### GET `/api/v1/monitoring/database/performance`

Get database performance metrics.

#### GET `/api/v1/monitoring/cache/stats`

Get cache performance statistics.

#### GET `/api/v1/monitoring/metrics/summary`

Get comprehensive metrics summary.

#### GET `/api/v1/monitoring/metrics/realtime`

Get real-time system metrics.

## Error Handling

The API uses standard HTTP status codes and provides detailed error information:

### HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters or body
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Error Types

#### ValidationError (400)
```json
{
  "error": "ValidationError",
  "message": "Invalid product name: must be at least 1 character",
  "field": "product_name",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### ProductNotFoundError (404)
```json
{
  "error": "ProductNotFoundError", 
  "message": "No products found matching 'xyz'",
  "suggestions": [
    "Try using more general product terms",
    "Check product name spelling"
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### QueryProcessingError (400)
```json
{
  "error": "QueryProcessingError",
  "message": "Failed to process natural language query",
  "query": "user's original query",
  "suggestions": [
    "Try rephrasing your query",
    "Use more specific product names"
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### RateLimitExceeded (429)
```json
{
  "error": "RateLimitExceeded",
  "message": "Rate limit exceeded: 10 requests per minute",
  "retry_after": 45,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Data Models

### QueryResult
```json
{
  "product_id": 123,
  "product_name": "Fresh Onions (1kg)",
  "platform_name": "Blinkit", 
  "current_price": 45.00,
  "original_price": 50.00,
  "discount_percentage": 10.0,
  "is_available": true,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

### ProductInfo
```json
{
  "id": 123,
  "name": "Fresh Onions (1kg)",
  "brand": "Farm Fresh",
  "category": "Vegetables",
  "description": "Fresh red onions",
  "pack_size": "1kg", 
  "is_organic": false
}
```

### ProductPrice
```json
{
  "platform_id": 1,
  "platform_name": "Blinkit",
  "current_price": 45.00,
  "original_price": 50.00,
  "discount_percentage": 10.0,
  "is_available": true,
  "stock_status": "in_stock",
  "delivery_time_minutes": 15,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

### DealInfo
```json
{
  "id": 456,
  "title": "30% Off on Fresh Vegetables",
  "description": "Get 30% discount on all fresh vegetables",
  "discount_type": "percentage",
  "discount_value": 30.0,
  "discount_percentage": 30.0,
  "max_discount_amount": 100.0,
  "min_order_amount": 200.0,
  "discount_code": "FRESH30",
  "platform_name": "Blinkit",
  "product_name": null,
  "category_name": "Vegetables",
  "original_price": 50.0,
  "discounted_price": 35.0,
  "savings_amount": 15.0,
  "is_featured": true,
  "start_date": "2024-01-15T00:00:00Z",
  "end_date": "2024-01-20T23:59:59Z",
  "usage_limit_per_user": 5
}
```

## OpenAPI/Swagger Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/v1/openapi.json`

## Performance Considerations

### Caching
- Query results are cached for 5 minutes by default
- Schema information is cached for 1 hour
- Cache hit ratios are monitored via `/api/v1/monitoring/cache/stats`

### Pagination
- Large result sets are automatically paginated
- Use `page` and `page_size` parameters for advanced queries
- Maximum page size is 100 results

### Sampling
- Statistical sampling is applied to very large datasets (>1000 results)
- Configurable sampling methods: random, systematic, stratified, top_n
- Sampling information is included in response metadata

## Best Practices

### Query Optimization
1. Use specific product names for better results
2. Include platform filters when comparing specific platforms
3. Use category filters to narrow search scope
4. Leverage caching by making similar queries within cache TTL

### Error Handling
1. Always check HTTP status codes
2. Parse error messages for specific guidance
3. Implement retry logic for rate limit errors (429)
4. Use suggestions provided in error responses

### Rate Limiting
1. Implement exponential backoff for rate limit errors
2. Cache responses locally when possible
3. Use batch operations where available
4. Monitor rate limit headers in responses

## Support and Contact

For API support, issues, or feature requests:
- Check the troubleshooting guide below
- Review error messages and suggestions
- Monitor system health via monitoring endpoints
- Implement proper error handling and retry logic

---

*This documentation is automatically generated from the FastAPI application. For the most up-to-date interactive documentation, visit the Swagger UI at `/docs`.*