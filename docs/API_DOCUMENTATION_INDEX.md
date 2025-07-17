# Quick Commerce Deals API - Complete Documentation

## Overview

Welcome to the comprehensive documentation for the Quick Commerce Deals API. This documentation provides everything you need to integrate with and use our price comparison platform effectively.

## Documentation Structure

### 📚 Core Documentation

1. **[API Documentation](API_DOCUMENTATION.md)** - Complete API reference
   - All endpoints with examples
   - Request/response schemas
   - Error handling
   - Rate limiting details
   - Authentication requirements

2. **[Natural Language Query Guide](NATURAL_LANGUAGE_QUERY_GUIDE.md)** - User guide for natural language queries
   - Query patterns and examples
   - Best practices for query optimization
   - Common use cases and workflows
   - Error handling and troubleshooting

3. **[LangChain Integration Guide](LANGCHAIN_INTEGRATION_GUIDE.md)** - Technical implementation details
   - Architecture overview
   - Custom SQL agent implementation
   - Semantic table indexing
   - Multi-step query processing
   - Performance optimization

4. **[Troubleshooting Guide & FAQ](TROUBLESHOOTING_FAQ.md)** - Problem resolution
   - Common issues and solutions
   - Error code reference
   - Performance troubleshooting
   - System monitoring
   - Getting help

### 🚀 Quick Start

#### 1. Interactive Documentation
Access the live, interactive API documentation:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON**: [http://localhost:8000/api/v1/openapi.json](http://localhost:8000/api/v1/openapi.json)

#### 2. First API Call
```bash
# Test the API with a simple health check
curl -X GET "http://localhost:8000/health"

# Try a natural language query
curl -X POST "http://localhost:8000/api/v1/query/" \
  -H "Content-Type: application/json" \
  -d '{"query": "Which app has cheapest onions right now?"}'
```

#### 3. Explore Sample Queries
```bash
# Find discounted products
curl -X POST "http://localhost:8000/api/v1/query/" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show products with 30%+ discount on Blinkit"}'

# Compare prices across platforms
curl -X GET "http://localhost:8000/api/v1/products/compare?product_name=milk&platforms=Blinkit,Zepto"

# Browse current deals
curl -X GET "http://localhost:8000/api/v1/deals/?min_discount=25&limit=10"
```

## API Features

### 🧠 Natural Language Processing
- Convert plain English queries to structured data
- Advanced LangChain v0.3+ integration
- Multi-step query validation and processing
- Intelligent table selection from 50+ database tables

### 🏪 Multi-Platform Support
- **Blinkit** - Quick grocery delivery
- **Zepto** - 10-minute delivery service
- **Instamart** - Swiggy's grocery platform
- **BigBasket Now** - Express grocery delivery
- **Additional platforms** - Extensible architecture

### 💰 Price Intelligence
- Real-time price tracking and comparison
- Discount and deal discovery
- Budget optimization recommendations
- Historical price analysis

### ⚡ Performance Features
- Redis-based caching system
- Connection pooling and optimization
- Statistical sampling for large datasets
- Intelligent query result pagination

### 📊 Monitoring & Analytics
- Comprehensive health monitoring
- Performance metrics and analytics
- Error tracking and alerting
- API usage statistics

## Use Cases

### 1. Consumer Price Comparison
```javascript
// Find the cheapest groceries
const response = await fetch('/api/v1/query/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: "Find cheapest vegetables for family of 4"
  })
});
```

### 2. Deal Discovery
```python
import requests

# Find current deals above 30% discount
response = requests.get(
    "http://localhost:8000/api/v1/deals/",
    params={
        "min_discount": 30,
        "featured_only": True,
        "limit": 20
    }
)
deals = response.json()
```

### 3. Budget Optimization
```bash
# Optimize grocery shopping within budget
curl -X POST "http://localhost:8000/api/v1/query/" \
  -H "Content-Type: application/json" \
  -d '{"query": "Best value groceries under ₹1500"}'
```

### 4. Platform Analytics
```python
# Compare platform performance
response = requests.post(
    "http://localhost:8000/api/v1/query/",
    json={"query": "Compare average prices between all platforms"}
)
```

## Integration Examples

### JavaScript/Node.js
```javascript
class QuickCommerceAPI {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }
  
  async naturalLanguageQuery(query, options = {}) {
    const response = await fetch(`${this.baseURL}/api/v1/query/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, ...options })
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  }
  
  async compareProducts(productName, platforms = []) {
    const params = new URLSearchParams({
      product_name: productName,
      ...(platforms.length && { platforms: platforms.join(',') })
    });
    
    const response = await fetch(
      `${this.baseURL}/api/v1/products/compare?${params}`
    );
    return response.json();
  }
}

// Usage
const api = new QuickCommerceAPI();
const results = await api.naturalLanguageQuery("cheapest milk prices");
```

### Python
```python
import requests
from typing import List, Optional, Dict

class QuickCommerceAPI:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def natural_language_query(self, query: str, **kwargs) -> Dict:
        """Execute natural language query"""
        response = self.session.post(
            f"{self.base_url}/api/v1/query/",
            json={"query": query, **kwargs}
        )
        response.raise_for_status()
        return response.json()
    
    def compare_products(self, product_name: str, 
                        platforms: Optional[List[str]] = None) -> Dict:
        """Compare product prices across platforms"""
        params = {"product_name": product_name}
        if platforms:
            params["platforms"] = ",".join(platforms)
        
        response = self.session.get(
            f"{self.base_url}/api/v1/products/compare",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_deals(self, min_discount: float = 0, **filters) -> Dict:
        """Get current deals and discounts"""
        params = {"min_discount": min_discount, **filters}
        response = self.session.get(
            f"{self.base_url}/api/v1/deals/",
            params=params
        )
        response.raise_for_status()
        return response.json()

# Usage
api = QuickCommerceAPI()
results = api.natural_language_query("Show me vegetable deals today")
```

### cURL Examples
```bash
#!/bin/bash

# Set base URL
BASE_URL="http://localhost:8000"

# Function to make natural language queries
query_api() {
    local query="$1"
    curl -s -X POST "$BASE_URL/api/v1/query/" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$query\"}" | jq '.'
}

# Function to compare products
compare_products() {
    local product="$1"
    local platforms="$2"
    curl -s -X GET "$BASE_URL/api/v1/products/compare" \
        -G -d "product_name=$product" \
        -d "platforms=$platforms" | jq '.'
}

# Usage examples
query_api "cheapest onions right now"
compare_products "milk" "Blinkit,Zepto"
```

## Error Handling Best Practices

### 1. Implement Retry Logic
```python
import time
import random

def make_request_with_retry(request_func, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = request_func()
            
            if response.status_code == 429:  # Rate limited
                retry_after = response.json().get('retry_after', 60)
                time.sleep(retry_after + random.uniform(0, 5))
                continue
            
            return response
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

### 2. Handle Different Error Types
```python
def handle_api_response(response):
    if response.status_code == 200:
        return response.json()
    
    error_data = response.json()
    error_type = error_data.get('error', 'Unknown')
    
    if error_type == 'ProductNotFoundError':
        # Use suggestions from API
        suggestions = error_data.get('suggestions', [])
        print(f"Product not found. Try: {', '.join(suggestions)}")
    
    elif error_type == 'QueryProcessingError':
        # Simplify query or use structured endpoints
        print("Query too complex. Try breaking it into simpler parts.")
    
    elif error_type == 'ValidationError':
        # Fix input validation issues
        field = error_data.get('field', 'unknown')
        print(f"Invalid {field}: {error_data['message']}")
    
    raise Exception(f"API Error: {error_data['message']}")
```

## Performance Optimization

### 1. Use Caching
```python
import hashlib
import json
from functools import lru_cache

class CachedQuickCommerceAPI(QuickCommerceAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}
    
    def _cache_key(self, method: str, **params) -> str:
        cache_data = {"method": method, "params": params}
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
    
    def natural_language_query(self, query: str, **kwargs):
        cache_key = self._cache_key("query", query=query, **kwargs)
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        result = super().natural_language_query(query, **kwargs)
        self.cache[cache_key] = result
        return result
```

### 2. Use Pagination
```python
def get_all_deals(api, min_discount=0, page_size=50):
    """Get all deals using pagination"""
    all_deals = []
    page = 1
    
    while True:
        response = api.session.get(
            f"{api.base_url}/api/v1/query/advanced",
            json={
                "query": f"show deals with {min_discount}%+ discount",
                "page": page,
                "page_size": page_size
            }
        )
        
        data = response.json()
        deals = data.get('results', [])
        
        if not deals:
            break
        
        all_deals.extend(deals)
        page += 1
    
    return all_deals
```

## Monitoring and Health Checks

### System Health Monitoring
```python
def monitor_api_health(api):
    """Monitor API health and performance"""
    try:
        # Check basic health
        health = api.session.get(f"{api.base_url}/health").json()
        print(f"API Status: {health['status']}")
        
        # Check detailed monitoring
        monitoring = api.session.get(
            f"{api.base_url}/api/v1/monitoring/health"
        ).json()
        
        for component, status in monitoring['components'].items():
            print(f"{component}: {status['status']} - {status['message']}")
        
        # Check performance metrics
        metrics = api.session.get(
            f"{api.base_url}/api/v1/monitoring/metrics/summary"
        ).json()
        
        print(f"System Efficiency: {metrics['summary']['system_efficiency_score']}%")
        
    except Exception as e:
        print(f"Health check failed: {e}")
```

## Support and Resources

### 📖 Documentation Links
- **[Complete API Reference](API_DOCUMENTATION.md)** - Detailed endpoint documentation
- **[Query Guide](NATURAL_LANGUAGE_QUERY_GUIDE.md)** - Natural language query patterns
- **[Technical Guide](LANGCHAIN_INTEGRATION_GUIDE.md)** - Implementation details
- **[Troubleshooting](TROUBLESHOOTING_FAQ.md)** - Problem resolution

### 🔧 Development Tools
- **Swagger UI**: Interactive API testing at `/docs`
- **ReDoc**: Alternative documentation at `/redoc`
- **Health Monitoring**: System status at `/api/v1/monitoring/health`
- **Performance Metrics**: Real-time metrics at `/api/v1/monitoring/metrics/realtime`

### 💡 Best Practices
1. **Start Simple**: Begin with basic queries and add complexity gradually
2. **Handle Errors**: Implement proper error handling with retry logic
3. **Use Caching**: Cache responses locally to improve performance
4. **Monitor Usage**: Track API usage and performance metrics
5. **Follow Rate Limits**: Implement proper rate limiting and backoff strategies

### 🆘 Getting Help
1. **Check Documentation**: Review relevant documentation sections
2. **Use Monitoring**: Check system health and performance metrics
3. **Review Logs**: Examine error messages and suggestions
4. **Test Incrementally**: Isolate issues with simple test cases
5. **Check Configuration**: Verify environment variables and settings

---

*This documentation is automatically updated with each API release. For the most current information, always refer to the interactive documentation at `/docs`.*