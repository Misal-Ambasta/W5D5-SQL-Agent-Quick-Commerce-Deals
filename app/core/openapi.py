"""
Enhanced OpenAPI documentation configuration
"""
from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI

def custom_openapi(app: FastAPI):
    """Generate custom OpenAPI schema with enhanced documentation"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Quick Commerce Deals API",
        version="1.0.0",
        description="""
# Quick Commerce Deals API

A comprehensive price comparison platform for quick commerce applications that enables users to track real-time pricing, discounts, and availability across multiple platforms using natural language queries.

## Features

- **Natural Language Processing**: Convert plain English queries to SQL using advanced LangChain integration
- **Multi-Platform Comparison**: Compare prices across Blinkit, Zepto, Instamart, BigBasket Now, and more
- **Real-time Data**: Access current pricing and availability information
- **Advanced Query Processing**: Multi-step query validation and optimization
- **Intelligent Caching**: High-performance caching with Redis integration
- **Comprehensive Monitoring**: Built-in performance monitoring and health checks

## Quick Start

### 1. Basic Natural Language Query
```bash
curl -X POST "http://localhost:8000/api/v1/query/" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "Which app has cheapest onions right now?"}'
```

### 2. Product Price Comparison
```bash
curl -X GET "http://localhost:8000/api/v1/products/compare?product_name=onions&platforms=Blinkit,Zepto"
```

### 3. Find Deals and Discounts
```bash
curl -X GET "http://localhost:8000/api/v1/deals/?min_discount=30&platform=Blinkit"
```

## Sample Queries

The API supports various natural language query patterns:

- **Price Comparison**: "Which app has cheapest onions right now?"
- **Discount Search**: "Show products with 30%+ discount on Blinkit"
- **Platform Comparison**: "Compare fruit prices between Zepto and Instamart"
- **Budget Optimization**: "Find best deals for ₹1000 grocery list"

## Rate Limits

- Natural Language Queries: 10 requests/minute
- Advanced Queries: 5 requests/minute
- Product Comparisons: 20 requests/minute
- Deals Endpoints: 30 requests/minute

## Error Handling

All endpoints return structured error responses with helpful suggestions:

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

## Monitoring

System health and performance can be monitored via dedicated endpoints:

- `/api/v1/monitoring/health` - System health check
- `/api/v1/monitoring/database/performance` - Database metrics
- `/api/v1/monitoring/cache/stats` - Cache performance

## Support

For detailed documentation, troubleshooting, and examples:
- **User Guide**: `/docs/NATURAL_LANGUAGE_QUERY_GUIDE.md`
- **Technical Guide**: `/docs/LANGCHAIN_INTEGRATION_GUIDE.md`
- **Troubleshooting**: `/docs/TROUBLESHOOTING_FAQ.md`
        """,
        routes=app.routes,
        servers=[
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            },
            {
                "url": "https://api.quickcommercedeals.com",
                "description": "Production server"
            }
        ],
        tags=[
            {
                "name": "query",
                "description": "Natural language query processing endpoints. Convert plain English queries to structured product data using advanced LangChain integration.",
                "externalDocs": {
                    "description": "Natural Language Query Guide",
                    "url": "/docs/NATURAL_LANGUAGE_QUERY_GUIDE.md"
                }
            },
            {
                "name": "products",
                "description": "Product comparison and search endpoints. Compare prices across platforms with detailed filtering options.",
                "externalDocs": {
                    "description": "Product Comparison Examples",
                    "url": "/docs/API_DOCUMENTATION.md#product-comparison"
                }
            },
            {
                "name": "deals",
                "description": "Deals and discount discovery endpoints. Find current promotions, discounts, and special offers across platforms.",
                "externalDocs": {
                    "description": "Deals API Examples",
                    "url": "/docs/API_DOCUMENTATION.md#deals-and-discounts"
                }
            },
            {
                "name": "monitoring",
                "description": "System monitoring and health check endpoints. Monitor API performance, database health, and system metrics.",
                "externalDocs": {
                    "description": "Monitoring Guide",
                    "url": "/docs/TROUBLESHOOTING_FAQ.md#system-monitoring"
                }
            }
        ]
    )
    
    # Add custom extensions
    openapi_schema["info"]["x-logo"] = {
        "url": "/static/logo.png",
        "altText": "Quick Commerce Deals API"
    }
    
    # Add contact information
    openapi_schema["info"]["contact"] = {
        "name": "API Support",
        "url": "https://github.com/quickcommercedeals/api",
        "email": "support@quickcommercedeals.com"
    }
    
    # Add license information
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "RateLimiting": {
            "type": "apiKey",
            "in": "header",
            "name": "X-RateLimit-Token",
            "description": "Optional rate limiting token for increased limits"
        }
    }
    
    # Add common response schemas
    openapi_schema["components"]["schemas"]["ErrorResponse"] = {
        "type": "object",
        "properties": {
            "error": {
                "type": "string",
                "description": "Error type identifier"
            },
            "message": {
                "type": "string",
                "description": "Human-readable error message"
            },
            "suggestions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Helpful suggestions to resolve the error"
            },
            "timestamp": {
                "type": "string",
                "format": "date-time",
                "description": "Error occurrence timestamp"
            }
        },
        "required": ["error", "message", "timestamp"]
    }
    
    openapi_schema["components"]["schemas"]["HealthResponse"] = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["healthy", "degraded", "unhealthy"],
                "description": "Overall system health status"
            },
            "timestamp": {
                "type": "string",
                "format": "date-time"
            },
            "version": {
                "type": "string",
                "description": "API version"
            },
            "components": {
                "type": "object",
                "description": "Individual component health status"
            }
        }
    }
    
    # Add example responses
    openapi_schema["components"]["examples"] = {
        "NaturalLanguageQueryExample": {
            "summary": "Basic natural language query",
            "value": {
                "query": "Which app has cheapest onions right now?"
            }
        },
        "AdvancedQueryExample": {
            "summary": "Advanced query with pagination",
            "value": {
                "query": "Show products with 30%+ discount on Blinkit",
                "user_id": "user123",
                "context": {
                    "location": "Mumbai",
                    "preferences": {"organic_only": False}
                }
            }
        },
        "ProductComparisonExample": {
            "summary": "Product comparison request",
            "value": {
                "product_name": "onions",
                "platforms": ["Blinkit", "Zepto"],
                "category": "Vegetables"
            }
        },
        "DealsRequestExample": {
            "summary": "Deals search request",
            "value": {
                "platform": "Blinkit",
                "category": "Vegetables",
                "min_discount": 30,
                "featured_only": True,
                "limit": 20
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def setup_openapi_docs(app: FastAPI):
    """Setup enhanced OpenAPI documentation"""
    app.openapi = lambda: custom_openapi(app)
    
    # Add custom CSS for documentation
    app.swagger_ui_parameters = {
        "deepLinking": True,
        "displayRequestDuration": True,
        "docExpansion": "none",
        "operationsSorter": "method",
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "tryItOutEnabled": True
    }