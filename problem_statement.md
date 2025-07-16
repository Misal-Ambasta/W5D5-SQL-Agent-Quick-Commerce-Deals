## Q: 2
### Quick Commerce Deals

You're building a price comparison platform for quick commerce apps (Blinkit, Zepto, Instamart, BigBasket Now, etc.) that tracks real-time pricing, discounts, and availability across multiple platforms for thousands of products using natural language queries.

---

## Core Requirements

- **Database Design**
  - Schema for products, prices, discounts, availability, platform data
  - Add as many tables as possible

- **Data Integration**
  - Simulate real-time price updates with dummy data across platforms

- **SQL Agent**
  - Handle complex multi-table queries with intelligent table selection

- **Performance**
  - Optimize for high-frequency updates and concurrent queries

---

## Technical Implementation Requirements

### Large-Scale Data Handling

- Implement semantic indexing for intelligent table selection from 50+ tables
- Build query planning system with optimal join path determination
- Create multi-step query generation with validation at each step
- Use statistical sampling and pagination for large result sets
- Integrate LangChain's `SQLDatabaseToolkit` with custom extensions
- Add schema caching and query result caching strategies
- Database connection pooling and query monitoring
- Query complexity analysis with automatic optimization

---

## Sample Queries

- "Which app has cheapest onions right now?"
- "Show products with 30%+ discount on Blinkit"
- "Compare fruit prices between Zepto and Instamart"
- "Find best deals for ₹1000 grocery list"

---

## Deliverables

- Working SQL agent with web interface
- Optimized database schema for multi-platform data
- Advanced query generation with intelligent table selection
- Basic security with rate limiting
- Architecture documentation
