# Quick Commerce Deals - Price Comparison Platform

A comprehensive price comparison platform for quick commerce applications (Blinkit, Zepto, Instamart, BigBasket Now, etc.) that enables users to track real-time pricing, discounts, and availability across multiple platforms using natural language queries.

## 🚀 Features

- **Natural Language Queries**: Ask questions like "Which app has cheapest onions right now?"
- **Multi-Platform Comparison**: Compare prices across Blinkit, Zepto, Instamart, and BigBasket Now
- **Real-time Price Tracking**: Simulated real-time price updates across platforms
- **Smart Deal Detection**: Find products with significant discounts and promotions
- **Intelligent Query Processing**: LangChain-powered SQL generation with semantic table selection
- **Advanced Query Optimization**: Multi-step query validation and semantic table indexing
- **Comprehensive Caching**: Redis-based multi-level caching for optimal performance
- **RESTful API**: FastAPI-based backend with automatic OpenAPI documentation
- **Modern React Interface**: React + TypeScript frontend with advanced filtering and real-time monitoring
- **Advanced Filtering System**: Apply filters with dedicated button for price range, platform, discounts, and availability
- **Real-time Monitoring Dashboard**: System health, performance metrics, and comprehensive analytics
- **50+ Database Tables**: Comprehensive schema covering products, pricing, discounts, and analytics

## Architecture

- **Backend**: FastAPI with LangChain v0.3+ for NLP-to-SQL conversion
- **Frontend**: React + TypeScript with Vite build system
- **Database**: PostgreSQL with 50+ tables for comprehensive product data
- **Cache**: Redis for query result and schema caching
- **AI**: Google Gemini 2.0 Flash integration for natural language processing

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+ and npm (for React frontend)
- Docker and Docker Compose (recommended)
- Google API Key (for Gemini AI)

**OR** (for manual setup):

- PostgreSQL
- Redis

### Installation

#### Option 1: Docker Setup (Recommended)

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd quick-commerce-deals
   ```

2. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your Google API key and other configuration
   ```

3. **Start all services with Docker Compose**

   ```bash
   # Start PostgreSQL and Redis in the background
   docker-compose up -d postgres redis

   # Wait for services to be ready (about 30 seconds)
   docker-compose logs postgres redis

   # Verify services are running
   docker-compose ps
   ```

4. **Set up database schema and sample data**

   ```bash
   # Create and activate virtual environment for setup scripts
   python -m venv venv

   # On Windows
   venv\Scripts\activate
   source venv/Scripts/activate

   # On macOS/Linux
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt

   # Run database setup scripts
   python scripts/setup_core_tables.py
   python scripts/setup_pricing_tables.py
   python scripts/setup_inventory_analytics_tables.py
   python scripts/generate_dummy_data.py
   ```

#### Option 2: Manual Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd quick-commerce-deals
   ```

2. **Create and activate virtual environment**

   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up PostgreSQL database**

   ```bash
   # Create PostgreSQL database
   createdb quick_commerce_deals

   # Run database setup scripts
   python scripts/setup_core_tables.py
   python scripts/setup_pricing_tables.py
   python scripts/setup_inventory_analytics_tables.py
   python scripts/generate_dummy_data.py
   ```

6. **Start Redis server**
   ```bash
   redis-server
   ```

### Running the Application

#### With Docker (Recommended)

1. **Start all services including the API**

   ```bash
   # Start all services (PostgreSQL, Redis, and FastAPI API)
   docker-compose up -d

   # View logs to ensure everything is running
   docker-compose logs -f api
   ```

   API will be available at http://localhost:8000

2. **Start the React frontend** (in a separate terminal)

   ```bash
   # Navigate to frontend directory
   cd frontend

   # Install Node.js dependencies
   npm install

   # Start the development server
   npm run dev
   ```

   Frontend will be available at http://localhost:5173

3. **Useful Docker commands**

   ```bash
   # Stop all services
   docker-compose down

   # View service status
   docker-compose ps

   # View logs for specific service
   docker-compose logs postgres
   docker-compose logs redis
   docker-compose logs api

   # Restart a specific service
   docker-compose restart postgres

   # Remove all containers and volumes (clean slate)
   docker-compose down -v
   ```

#### Manual Setup

1. **Start the FastAPI backend**

   ```bash
   python run_api.py
   ```

   API will be available at http://localhost:8000

2. **Start the React frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Frontend will be available at http://localhost:5173

## Configuration

### Environment Variables

| Variable                | Description                       | Default              |
| ----------------------- | --------------------------------- | -------------------- |
| `POSTGRES_SERVER`       | PostgreSQL server host            | localhost            |
| `POSTGRES_USER`         | PostgreSQL username               | postgres             |
| `POSTGRES_PASSWORD`     | PostgreSQL password               | postgres             |
| `POSTGRES_DB`           | PostgreSQL database name          | quick_commerce_deals |
| `POSTGRES_PORT`         | PostgreSQL server port            | 5432                 |
| `REDIS_HOST`            | Redis server host                 | localhost            |
| `REDIS_PORT`            | Redis server port                 | 6379                 |
| `REDIS_DB`              | Redis database number             | 0                    |
| `GOOGLE_API_KEY`        | Google API key for Gemini AI      | -                    |
| `SECRET_KEY`            | Application secret key            | -                    |
| `RATE_LIMIT_PER_MINUTE` | API rate limiting                 | 60                   |
| `CACHE_TTL_SECONDS`     | Cache time-to-live                | 300                  |
| `DB_POOL_SIZE`          | Database connection pool size     | 10                   |
| `DB_MAX_OVERFLOW`       | Database max overflow connections | 20                   |

### Getting Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key
5. Add it to your `.env` file as `GOOGLE_API_KEY=your-api-key-here`

## 📖 Usage Examples

### Web Interface (React)

1. **Access the web interface** at http://localhost:5173
2. **Enter natural language queries** in the search box
3. **Use advanced filtering options**:
   - **Platform Filter**: Select specific platforms (All, Blinkit, Zepto, etc.)
   - **Price Range**: Use dual sliders to set min/max price
   - **Discount Filter**: Set minimum discount percentage
   - **Availability Filter**: Filter by stock status
   - **Sorting Options**: Sort by price, discount, product name, or platform
4. **Apply filters**: Click "Apply Filters" button to apply all selected filters
5. **Reset filters**: Click "Reset All" to clear all filters
6. **View results** with price comparisons and visualizations
7. **Switch between views**: Table view or Card view for results
8. **Monitor system health**: Access the monitoring dashboard for real-time metrics

### React Frontend Features

#### Advanced Filtering System
- **Dual-range sliders** for precise price filtering
- **Platform selection** with dropdown
- **Discount percentage** input with validation
- **Availability status** filtering
- **Apply/Reset buttons** for controlled filter application

#### Real-time Monitoring Dashboard
- **System Health**: Database, cache, and API status
- **Performance Metrics**: Response times, query statistics
- **Real-time Charts**: Auto-refreshing performance data
- **Alert System**: Notifications for system issues

#### Product Comparison Views
- **Table View**: Comprehensive data in sortable columns
- **Card View**: Visual product cards with deal highlights
- **Best Deal Highlighting**: Automatic best deal identification

### API Usage

#### Natural Language Query Processing

```bash
# Example: Find cheapest onions
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Which app has cheapest onions right now?",
    "max_results": 10
  }'
```

Response:
```json
{
  "query": "Which app has cheapest onions right now?",
  "results": [
    {
      "product_name": "Red Onions",
      "platform": "Blinkit",
      "current_price": 25.50,
      "original_price": 30.00,
      "discount_percentage": 15.0,
      "is_available": true
    }
  ],
  "execution_time": 0.85,
  "relevant_tables": ["products", "current_prices", "platforms"],
  "total_results": 5,
  "cached": false
}
```

#### Product Price Comparison

```bash
# Compare specific product across platforms
curl "http://localhost:8000/api/v1/products/compare?product_name=onions&platforms=blinkit,zepto"
```

Response:
```json
{
  "product_name": "onions",
  "platforms": [
    {
      "platform": "Blinkit",
      "price": 25.50,
      "discount": 15.0,
      "available": true
    },
    {
      "platform": "Zepto",
      "price": 28.00,
      "discount": 10.0,
      "available": true
    }
  ],
  "best_deal": {
    "platform": "Blinkit",
    "price": 25.50,
    "savings": 2.50
  },
  "savings_potential": 2.50
}
```

#### Get Current Deals

```bash
# Get deals with minimum discount
curl "http://localhost:8000/api/v1/deals?platform=blinkit&min_discount=30"
```

### Sample Queries

#### Basic Price Queries
- "Which app has cheapest onions right now?"
- "Show me tomato prices on all platforms"
- "What's the price of milk on Zepto?"

#### Discount and Deal Queries
- "Show products with 30%+ discount on Blinkit"
- "Find all items on sale at Instamart"
- "Which platform has the best deals today?"

#### Comparison Queries
- "Compare fruit prices between Zepto and Instamart"
- "Show price difference for vegetables across all apps"
- "Which app is cheaper for dairy products?"

#### Budget Optimization Queries
- "Find best deals for ₹1000 grocery list"
- "Show cheapest way to buy fruits worth ₹500"
- "Optimize my shopping for maximum savings"

#### Category-based Queries
- "Show all discounted fruits on BigBasket Now"
- "Compare snack prices across platforms"
- "Find cheapest cleaning products"

## 🔌 API Documentation

### Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

### Authentication
Currently, the API uses rate limiting based on IP address. No authentication is required for basic usage.

### Rate Limiting
- **Default**: 60 requests per minute per IP
- **Headers**: Rate limit information is included in response headers
  - `X-RateLimit-Limit`: Maximum requests per window
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time when the rate limit resets

### Endpoints

#### 1. Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "database": "connected",
  "cache": "connected"
}
```

#### 2. API Information
```http
GET /
```

**Response:**
```json
{
  "name": "Quick Commerce Deals API",
  "version": "1.0.0",
  "description": "Price comparison platform for quick commerce apps",
  "docs_url": "/docs"
}
```

#### 3. Natural Language Query
```http
POST /api/v1/query
```

**Request Body:**
```json
{
  "query": "string (required)",
  "user_id": "string (optional)",
  "context": "object (optional)",
  "max_results": "integer (optional, default: 100)"
}
```

**Response:**
```json
{
  "query": "string",
  "results": "array",
  "execution_time": "float",
  "relevant_tables": "array",
  "total_results": "integer",
  "cached": "boolean",
  "suggestions": "array (optional)"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid query format
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Query processing failed

#### 4. Product Comparison
```http
GET /api/v1/products/compare
```

**Query Parameters:**
- `product_name` (required): Name of the product to compare
- `platforms` (optional): Comma-separated list of platforms
- `category` (optional): Product category filter

**Response:**
```json
{
  "product_name": "string",
  "platforms": [
    {
      "platform": "string",
      "price": "number",
      "original_price": "number",
      "discount_percentage": "number",
      "is_available": "boolean",
      "last_updated": "datetime"
    }
  ],
  "best_deal": "object",
  "savings_potential": "number"
}
```

#### 5. Current Deals
```http
GET /api/v1/deals
```

**Query Parameters:**
- `platform` (optional): Filter by specific platform
- `category` (optional): Filter by product category
- `min_discount` (optional): Minimum discount percentage
- `limit` (optional): Maximum number of results (default: 50)

**Response:**
```json
{
  "deals": [
    {
      "product_name": "string",
      "platform": "string",
      "current_price": "number",
      "original_price": "number",
      "discount_percentage": "number",
      "savings": "number",
      "valid_until": "datetime"
    }
  ],
  "total_deals": "integer",
  "filters_applied": "object"
}
```

#### 6. System Monitoring
```http
GET /api/v1/monitoring/health
GET /api/v1/monitoring/metrics
GET /api/v1/monitoring/database/performance
GET /api/v1/monitoring/cache/stats
```

### Interactive API Documentation

Once the API is running, you can access interactive documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- Explore all available endpoints
- Test API calls directly from the browser
- View detailed request/response schemas
- Download OpenAPI specification

## Troubleshooting

### Docker Issues

**Services not starting:**

```bash
# Check if ports are already in use
netstat -tulpn | grep :5432  # PostgreSQL
netstat -tulpn | grep :6379  # Redis
netstat -tulpn | grep :8000  # FastAPI

# Stop conflicting services
sudo systemctl stop postgresql
sudo systemctl stop redis-server

# Restart Docker services
docker-compose down
docker-compose up -d
```

**Database connection issues:**

```bash
# Check if PostgreSQL is ready
docker-compose exec postgres pg_isready -U postgres

# View PostgreSQL logs
docker-compose logs postgres

# Connect to database directly
docker-compose exec postgres psql -U postgres -d quick_commerce_deals
```

**Redis connection issues:**

```bash
# Check Redis connectivity
docker-compose exec redis redis-cli ping

# View Redis logs
docker-compose logs redis
```

### Frontend Issues

**React development server not starting:**

```bash
# Navigate to frontend directory
cd frontend

# Clean node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Start development server
npm run dev
```

**Frontend build issues:**

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### API Issues

**Google API Key errors:**

- Ensure your `GOOGLE_API_KEY` is set in the `.env` file
- Verify the API key is valid at [Google AI Studio](https://makersuite.google.com/app/apikey)
- Check API quotas and billing settings

**Database schema errors:**

```bash
# Re-run database setup scripts
python scripts/setup_core_tables.py
python scripts/setup_pricing_tables.py
python scripts/setup_inventory_analytics_tables.py
```

**Port conflicts:**

```bash
# Use different ports if needed
docker-compose down
# Edit docker-compose.yml to change port mappings
# For example: "5433:5432" instead of "5432:5432"
docker-compose up -d
```

### Performance Tips

- **Database Performance**: The system includes 50+ tables with sample data. Initial queries may be slower until indexes are warmed up.
- **Cache Warming**: Redis cache improves performance after the first few queries.
- **Rate Limiting**: API is rate-limited to 60 requests per minute by default.
- **Memory Usage**: Ensure Docker has at least 4GB RAM allocated for optimal performance.
- **Frontend Performance**: React development server includes hot reloading for faster development.

## Development

### Project Structure

```
quick-commerce-deals/
├── app/                    # FastAPI application
│   ├── api/               # API routes
│   ├── core/              # Core configuration
│   ├── db/                # Database models and utilities
│   ├── models/            # Pydantic models
│   └── services/          # Business logic services
├── frontend/              # React + TypeScript frontend
│   ├── src/               # Source code
│   │   ├── components/    # React components
│   │   ├── App.tsx        # Main application component
│   │   └── main.tsx       # Application entry point
│   ├── public/            # Static assets
│   └── package.json       # Node.js dependencies
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
isort .
flake8 .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License.