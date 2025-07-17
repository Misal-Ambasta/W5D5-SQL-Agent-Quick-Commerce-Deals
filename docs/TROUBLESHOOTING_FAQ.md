# Troubleshooting Guide and FAQ

## Table of Contents

1. [Common Issues and Solutions](#common-issues-and-solutions)
2. [API Error Codes](#api-error-codes)
3. [Query Processing Issues](#query-processing-issues)
4. [Database Connection Problems](#database-connection-problems)
5. [Performance Issues](#performance-issues)
6. [Rate Limiting Issues](#rate-limiting-issues)
7. [LangChain Integration Issues](#langchain-integration-issues)
8. [Frequently Asked Questions](#frequently-asked-questions)
9. [System Monitoring](#system-monitoring)
10. [Getting Help](#getting-help)

## Common Issues and Solutions

### 1. No Results Found for Query

**Symptoms:**
- API returns empty results array
- Response includes suggestions for alternative queries

**Common Causes:**
- Product name misspelled or not in database
- Too specific filters applied
- Product not available on any platform
- Query syntax not recognized

**Solutions:**

```bash
# Check if product exists in database
curl -X GET "http://localhost:8000/api/v1/products/compare?product_name=onion"

# Try more general terms
# Instead of: "organic red onions 1kg"
# Try: "onions"

# Remove platform filters
# Instead of: "cheapest onions on XYZ platform"
# Try: "cheapest onions"
```

**Prevention:**
- Use the suggestions provided in the API response
- Start with simple queries and add complexity gradually
- Check product availability using the monitoring endpoints

### 2. Query Processing Timeout

**Symptoms:**
- Request takes longer than expected
- Timeout errors in API response
- High execution times in response metadata

**Common Causes:**
- Complex multi-table queries
- Large result sets without pagination
- Database performance issues
- LangChain API delays

**Solutions:**

```python
# Use advanced query endpoint with pagination
import requests

response = requests.post(
    "http://localhost:8000/api/v1/query/advanced",
    json={
        "query": "your complex query",
        "page": 1,
        "page_size": 20,
        "sampling_method": "random",
        "sample_size": 100
    }
)
```

**Prevention:**
- Use pagination for large result sets
- Apply sampling for very large datasets
- Monitor query performance via `/api/v1/monitoring/database/performance`

### 3. Rate Limit Exceeded

**Symptoms:**
- HTTP 429 status code
- "Rate limit exceeded" error message
- `retry_after` field in response

**Solutions:**

```python
import time
import requests

def make_request_with_retry(url, data, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post(url, json=data)
        
        if response.status_code == 429:
            retry_after = response.json().get('retry_after', 60)
            print(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

**Prevention:**
- Implement exponential backoff
- Cache responses locally
- Use batch operations where possible
- Monitor rate limit headers

### 4. Database Connection Errors

**Symptoms:**
- "Database connection failed" errors
- Health check endpoint shows database as unhealthy
- Intermittent connection issues

**Common Causes:**
- Database server down
- Connection pool exhausted
- Network connectivity issues
- Invalid database credentials

**Solutions:**

```bash
# Check database health
curl -X GET "http://localhost:8000/api/v1/monitoring/health"

# Check database performance
curl -X GET "http://localhost:8000/api/v1/monitoring/database/performance"

# Restart database connection pool
# This would typically require application restart
```

**Prevention:**
- Monitor database health regularly
- Configure appropriate connection pool sizes
- Implement database failover mechanisms
- Set up database monitoring alerts

## API Error Codes

### HTTP Status Codes

| Code | Status | Description | Action Required |
|------|--------|-------------|-----------------|
| 200 | OK | Request successful | None |
| 400 | Bad Request | Invalid request parameters | Check request format |
| 404 | Not Found | Resource not found | Verify resource exists |
| 422 | Unprocessable Entity | Validation error | Fix validation issues |
| 429 | Too Many Requests | Rate limit exceeded | Implement retry logic |
| 500 | Internal Server Error | Server error | Check logs, retry |
| 503 | Service Unavailable | Service temporarily down | Wait and retry |

### Custom Error Types

#### ValidationError (400)

```json
{
  "error": "ValidationError",
  "message": "Invalid product name: must be at least 1 character",
  "field": "product_name",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Solutions:**
- Check input validation requirements
- Ensure all required fields are provided
- Verify data types match expected formats

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

**Solutions:**
- Use suggestions provided in response
- Try alternative product names
- Check product catalog via comparison endpoints

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

**Solutions:**
- Rephrase query using suggestions
- Break complex queries into simpler parts
- Use structured endpoints for complex comparisons

## Query Processing Issues

### 1. LangChain SQL Generation Failures

**Symptoms:**
- "SQL generation failed" errors
- Queries return unexpected results
- Complex queries not processed correctly

**Debugging Steps:**

```python
# Enable verbose logging to see SQL generation process
import logging
logging.getLogger('langchain').setLevel(logging.DEBUG)

# Test with simpler queries first
simple_queries = [
    "show onion prices",
    "find cheapest milk",
    "compare apple prices"
]

for query in simple_queries:
    response = requests.post(
        "http://localhost:8000/api/v1/query/",
        json={"query": query}
    )
    print(f"Query: {query}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
```

**Solutions:**
- Use more specific product names
- Avoid overly complex natural language
- Try structured endpoints for complex queries
- Check LangChain API key and quotas

### 2. Semantic Table Selection Issues

**Symptoms:**
- Irrelevant tables selected for queries
- Poor query performance due to unnecessary joins
- Missing relevant data in results

**Debugging:**

```bash
# Check which tables are being selected
curl -X POST "http://localhost:8000/api/v1/query/" \
  -H "Content-Type: application/json" \
  -d '{"query": "your query here"}'

# Look at the "relevant_tables" field in response
```

**Solutions:**
- Rebuild semantic indexes if needed
- Adjust similarity thresholds in configuration
- Use more specific query terms
- Check table descriptions in semantic indexer

### 3. Multi-Step Query Processing Failures

**Symptoms:**
- Complex queries fail at intermediate steps
- Partial results returned
- Step validation errors

**Debugging:**

```python
# Use advanced endpoint to see step-by-step processing
response = requests.post(
    "http://localhost:8000/api/v1/query/advanced",
    json={
        "query": "complex query here",
        "result_format": "structured"
    }
)

# Check metadata for step information
metadata = response.json().get('metadata', {})
print(f"Steps executed: {metadata}")
```

## Database Connection Problems

### Connection Pool Exhaustion

**Symptoms:**
- "No available connections" errors
- Slow response times
- Connection timeout errors

**Monitoring:**

```bash
# Check connection pool status
curl -X GET "http://localhost:8000/api/v1/monitoring/database/performance"
```

**Solutions:**

```python
# Adjust connection pool settings in configuration
DATABASE_CONFIG = {
    'pool_size': 30,        # Increase pool size
    'max_overflow': 50,     # Increase overflow
    'pool_timeout': 30,     # Increase timeout
    'pool_recycle': 3600    # Recycle connections hourly
}
```

### Slow Query Performance

**Symptoms:**
- High execution times
- Database performance alerts
- Slow query logs

**Monitoring:**

```bash
# Check slow queries
curl -X GET "http://localhost:8000/api/v1/monitoring/database/slow-queries?limit=10"
```

**Solutions:**
- Add database indexes for frequently queried columns
- Optimize query patterns
- Use result caching
- Implement query result sampling

## Performance Issues

### High Memory Usage

**Symptoms:**
- Out of memory errors
- Slow response times
- System resource alerts

**Monitoring:**

```bash
# Check system resources
curl -X GET "http://localhost:8000/api/v1/monitoring/system/resources"
```

**Solutions:**
- Implement result pagination
- Use sampling for large datasets
- Optimize caching strategies
- Increase system memory if needed

### Cache Performance Issues

**Symptoms:**
- Low cache hit ratios
- Repeated expensive queries
- High database load

**Monitoring:**

```bash
# Check cache statistics
curl -X GET "http://localhost:8000/api/v1/monitoring/cache/stats"
```

**Solutions:**
- Adjust cache TTL values
- Optimize cache key generation
- Implement cache warming strategies
- Monitor cache memory usage

## Rate Limiting Issues

### Understanding Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/v1/query/` | 10 requests | per minute |
| `/api/v1/query/advanced` | 5 requests | per minute |
| `/api/v1/products/compare` | 20 requests | per minute |
| `/api/v1/deals/` | 30 requests | per minute |

### Implementing Retry Logic

```python
import time
import random

class RateLimitHandler:
    def __init__(self, base_delay=1, max_delay=60, backoff_factor=2):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
    
    def make_request_with_backoff(self, request_func, max_retries=5):
        for attempt in range(max_retries):
            try:
                response = request_func()
                
                if response.status_code == 429:
                    if attempt == max_retries - 1:
                        raise Exception("Max retries exceeded")
                    
                    # Exponential backoff with jitter
                    delay = min(
                        self.base_delay * (self.backoff_factor ** attempt),
                        self.max_delay
                    )
                    jitter = random.uniform(0, delay * 0.1)
                    time.sleep(delay + jitter)
                    continue
                
                return response
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(self.base_delay)
        
        raise Exception("Request failed after all retries")
```

## LangChain Integration Issues

### OpenAI API Issues

**Symptoms:**
- "OpenAI API error" messages
- Authentication failures
- Quota exceeded errors

**Solutions:**

```bash
# Check OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Verify API key is valid
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

**Common Issues:**
- Invalid or expired API key
- Insufficient API credits
- Rate limits on OpenAI API
- Model availability issues

### LangChain Configuration Issues

**Symptoms:**
- LangChain initialization failures
- SQL generation errors
- Agent execution failures

**Debugging:**

```python
# Test LangChain configuration
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase

# Test LLM connection
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
response = llm.invoke("Hello, world!")
print(response)

# Test database connection
db = SQLDatabase.from_uri("your-database-uri")
print(db.get_usable_table_names())
```

## Frequently Asked Questions

### Q: How do I improve query accuracy?

**A:** Follow these best practices:
- Use specific product names
- Include platform names when comparing
- Use category filters to narrow scope
- Start with simple queries and add complexity
- Review suggestions in error responses

### Q: Why are my queries slow?

**A:** Common causes and solutions:
- **Large result sets**: Use pagination and sampling
- **Complex queries**: Break into simpler parts
- **Database performance**: Check slow query logs
- **Network latency**: Implement local caching

### Q: How do I handle rate limits in production?

**A:** Implement proper rate limiting strategies:
- Use exponential backoff with jitter
- Cache responses locally
- Implement request queuing
- Monitor rate limit headers
- Consider upgrading rate limits if needed

### Q: What should I do if the database is unavailable?

**A:** Implement graceful degradation:
- Check health endpoint regularly
- Implement circuit breaker pattern
- Use cached data when available
- Provide meaningful error messages to users
- Set up monitoring alerts

### Q: How do I optimize for high traffic?

**A:** Scale your implementation:
- Implement horizontal scaling
- Use load balancing
- Optimize database queries
- Implement comprehensive caching
- Monitor system resources

### Q: Can I customize the natural language processing?

**A:** Yes, several customization options:
- Adjust semantic similarity thresholds
- Modify table descriptions for better context
- Customize query processing steps
- Add domain-specific vocabulary
- Train custom embeddings

### Q: How do I monitor system health?

**A:** Use the monitoring endpoints:
- `/api/v1/monitoring/health` - Overall system health
- `/api/v1/monitoring/database/performance` - Database metrics
- `/api/v1/monitoring/cache/stats` - Cache performance
- `/api/v1/monitoring/metrics/summary` - Comprehensive metrics

### Q: What data formats are supported?

**A:** The API supports:
- **Input**: JSON request bodies, URL query parameters
- **Output**: JSON responses with structured data
- **Export**: CSV and JSON export via Streamlit interface
- **Caching**: Redis-compatible serialization

### Q: How do I handle errors in production?

**A:** Implement comprehensive error handling:
- Parse error types and messages
- Use suggestions provided in responses
- Implement retry logic for transient errors
- Log errors for debugging
- Provide user-friendly error messages

### Q: Can I use the API without natural language queries?

**A:** Yes, use structured endpoints:
- `/api/v1/products/compare` - Direct product comparison
- `/api/v1/deals/` - Browse deals with filters
- Use query parameters for precise filtering
- Combine multiple endpoint calls for complex workflows

## System Monitoring

### Health Check Endpoints

```bash
# Basic health check
curl -X GET "http://localhost:8000/health"

# Comprehensive health check
curl -X GET "http://localhost:8000/api/v1/monitoring/health"

# Database performance
curl -X GET "http://localhost:8000/api/v1/monitoring/database/performance"

# Real-time metrics
curl -X GET "http://localhost:8000/api/v1/monitoring/metrics/realtime"
```

### Setting Up Monitoring Alerts

```python
# Example monitoring script
import requests
import time
import logging

def monitor_system_health():
    try:
        response = requests.get("http://localhost:8000/api/v1/monitoring/health")
        health_data = response.json()
        
        if health_data['status'] != 'healthy':
            logging.warning(f"System health degraded: {health_data}")
            # Send alert notification
        
        # Check specific components
        for component, status in health_data['components'].items():
            if status['status'] != 'healthy':
                logging.error(f"Component {component} unhealthy: {status}")
        
    except Exception as e:
        logging.error(f"Health check failed: {e}")

# Run monitoring every 5 minutes
while True:
    monitor_system_health()
    time.sleep(300)
```

### Performance Monitoring

```bash
# Monitor query performance
curl -X GET "http://localhost:8000/api/v1/monitoring/database/slow-queries"

# Check cache performance
curl -X GET "http://localhost:8000/api/v1/monitoring/cache/stats"

# System resource usage
curl -X GET "http://localhost:8000/api/v1/monitoring/system/resources"
```

## Getting Help

### Debug Information to Collect

When reporting issues, include:

1. **Request Details**:
   - Full request URL and body
   - HTTP method used
   - Headers sent

2. **Response Details**:
   - HTTP status code
   - Complete response body
   - Response headers

3. **System Information**:
   - API version
   - System health status
   - Recent error logs

4. **Environment Details**:
   - Database configuration
   - Cache configuration
   - System resources

### Log Analysis

```bash
# Check application logs
tail -f logs/app.log

# Check error logs
tail -f logs/errors.log

# Check API access logs
tail -f logs/api_access.log

# Filter for specific errors
grep "QueryProcessingError" logs/errors.log
```

### Performance Profiling

```python
# Enable detailed logging for debugging
import logging

# Set up comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable LangChain debugging
logging.getLogger('langchain').setLevel(logging.DEBUG)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### Contact and Support

For additional support:

1. **Check Documentation**: Review API documentation and guides
2. **Monitor System Health**: Use monitoring endpoints to diagnose issues
3. **Review Logs**: Check application and error logs for details
4. **Test with Simple Queries**: Isolate issues with basic functionality
5. **Check Configuration**: Verify all environment variables and settings

---

*This troubleshooting guide covers the most common issues and solutions. For specific technical problems, refer to the system logs and monitoring endpoints for detailed diagnostic information.*