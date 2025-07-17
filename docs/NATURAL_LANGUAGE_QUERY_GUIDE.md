# Natural Language Query Guide

## Overview

The Quick Commerce Deals platform supports natural language queries that are automatically converted to SQL queries using advanced LangChain integration. This guide provides comprehensive examples and patterns for effective querying.

## Supported Query Types

### 1. Price Comparison Queries

#### Finding Cheapest Products
**Pattern**: "Which app has cheapest [product] right now?"

**Examples**:
```
"Which app has cheapest onions right now?"
"Where can I find the cheapest milk?"
"Show me the cheapest bread across all platforms"
"Which platform has the lowest price for tomatoes?"
```

**What it does**:
- Searches across all active platforms
- Returns products sorted by price (lowest first)
- Shows current availability status
- Includes discount information if applicable

#### Price Range Queries
**Pattern**: "Show [product] under ₹[amount]" or "Find [product] between ₹[min] and ₹[max]"

**Examples**:
```
"Show onions under ₹50"
"Find milk between ₹40 and ₹60"
"List vegetables under ₹30 per kg"
"Show fruits priced between ₹100 and ₹200"
```

### 2. Discount and Deal Queries

#### Percentage-Based Discounts
**Pattern**: "Show products with [X]%+ discount on [platform]"

**Examples**:
```
"Show products with 30%+ discount on Blinkit"
"Find items with 50% or more discount on Zepto"
"List all products with 25%+ discount on Instamart"
"Show me deals with 40% discount on BigBasket Now"
```

#### Deal Discovery
**Pattern**: "Find best deals for [category/product]"

**Examples**:
```
"Find best deals for vegetables"
"Show me fruit deals today"
"What are the best grocery deals right now?"
"Find discount offers on dairy products"
```

### 3. Platform Comparison Queries

#### Direct Platform Comparison
**Pattern**: "Compare [product] prices between [platform1] and [platform2]"

**Examples**:
```
"Compare fruit prices between Zepto and Instamart"
"Show onion prices on Blinkit vs BigBasket"
"Compare milk prices across Zepto and Swiggy Instamart"
"Which is cheaper for vegetables - Blinkit or Zepto?"
```

#### Multi-Platform Analysis
**Pattern**: "Show [product] prices across all platforms"

**Examples**:
```
"Show apple prices across all platforms"
"Compare bread prices on all apps"
"List tomato prices from every platform"
"Show me rice prices everywhere"
```

### 4. Budget Optimization Queries

#### Budget-Based Shopping
**Pattern**: "Find best deals for ₹[amount] grocery list"

**Examples**:
```
"Find best deals for ₹1000 grocery list"
"Optimize my ₹500 shopping budget"
"What can I buy with ₹750 for groceries?"
"Best value groceries under ₹1200"
```

#### Value Optimization
**Pattern**: "Maximize savings for [category] shopping"

**Examples**:
```
"Maximize savings for vegetable shopping"
"Best value for money fruits"
"Most economical dairy products"
"Optimize spending on household items"
```

### 5. Category-Based Queries

#### Category Exploration
**Pattern**: "Show all [category] deals" or "Find [category] discounts"

**Examples**:
```
"Show all vegetable deals"
"Find fruit discounts today"
"List dairy product offers"
"Show snack deals across platforms"
```

#### Category Comparison
**Pattern**: "Compare [category] prices across platforms"

**Examples**:
```
"Compare vegetable prices across platforms"
"Show fruit price differences between apps"
"Compare dairy prices on all platforms"
"Which app has better snack prices?"
```

### 6. Availability and Stock Queries

#### Stock Status
**Pattern**: "What's available on [platform] right now?"

**Examples**:
```
"What's available on Blinkit right now?"
"Show in-stock items on Zepto"
"List available products on Instamart"
"What can I order from BigBasket Now?"
```

#### Out of Stock Alternatives
**Pattern**: "Find alternatives for [product] if out of stock"

**Examples**:
```
"Find alternatives for onions if out of stock"
"Show substitute products for milk"
"What can replace tomatoes if unavailable?"
"Alternative options for bread"
```

## Advanced Query Patterns

### 1. Time-Based Queries

**Examples**:
```
"Show today's best deals"
"Find weekend offers"
"What discounts are ending soon?"
"Show new deals this week"
```

### 2. Quantity-Based Queries

**Examples**:
```
"Find bulk deals for rice"
"Show family pack offers"
"Compare per kg prices for vegetables"
"Best value for large quantity purchases"
```

### 3. Brand-Specific Queries

**Examples**:
```
"Show Amul products across platforms"
"Compare Britannia prices on different apps"
"Find Tata brand deals"
"Show organic brand options"
```

### 4. Location-Based Queries (if supported)

**Examples**:
```
"Show deals available in my area"
"Find fastest delivery options"
"Compare delivery charges across platforms"
"Show same-day delivery deals"
```

## Query Optimization Tips

### 1. Be Specific
- ✅ "Show onion prices on Blinkit and Zepto"
- ❌ "Show prices"

### 2. Use Clear Product Names
- ✅ "Find milk 1L prices"
- ❌ "Find white liquid prices"

### 3. Include Relevant Context
- ✅ "Compare organic vegetable prices"
- ❌ "Compare prices"

### 4. Specify Platforms When Needed
- ✅ "Show Blinkit deals above 30% discount"
- ❌ "Show deals"

## Common Query Patterns and Results

### Pattern: Cheapest Product Query
**Input**: "Which app has cheapest onions right now?"

**Expected Results**:
- List of onion products sorted by price
- Platform names with current prices
- Availability status
- Discount information if applicable
- Last updated timestamps

### Pattern: Discount Query
**Input**: "Show products with 30%+ discount on Blinkit"

**Expected Results**:
- Products with discount ≥ 30%
- Original and discounted prices
- Savings amount
- Deal expiry information
- Product categories

### Pattern: Comparison Query
**Input**: "Compare fruit prices between Zepto and Instamart"

**Expected Results**:
- Side-by-side price comparison
- Best deal highlighting
- Savings potential
- Availability on each platform
- Price difference calculations

### Pattern: Budget Query
**Input**: "Find best deals for ₹1000 grocery list"

**Expected Results**:
- Optimized product selection
- Total cost breakdown
- Maximum savings achieved
- Alternative combinations
- Platform recommendations

## Error Handling and Suggestions

### Common Issues and Solutions

#### 1. No Results Found
**Possible Causes**:
- Product name misspelled
- Product not available on any platform
- Too specific filters applied

**Solutions**:
- Check spelling
- Use more general terms
- Remove some filters
- Try alternative product names

#### 2. Ambiguous Queries
**Examples of Ambiguous Queries**:
- "Show prices" (missing product)
- "Find deals" (too general)
- "Compare apps" (missing product/category)

**How to Improve**:
- Add specific product names
- Include platform names
- Specify categories or price ranges

#### 3. Query Too Complex
**Examples**:
- Very long queries with multiple conditions
- Nested comparisons
- Complex logical operations

**Solutions**:
- Break into simpler queries
- Use advanced query endpoint with parameters
- Focus on one main comparison at a time

## Best Practices

### 1. Start Simple
Begin with basic queries and gradually add complexity:
```
1. "Show onion prices"
2. "Show onion prices on Blinkit"
3. "Compare onion prices between Blinkit and Zepto"
4. "Find cheapest onions with 20%+ discount"
```

### 2. Use Natural Language
The system understands conversational queries:
- "What's the cheapest milk available?"
- "Where can I find the best vegetable deals?"
- "Show me discounted fruits on Zepto"

### 3. Be Patient with Complex Queries
Complex queries may take longer to process due to:
- Multi-table joins
- Large result sets
- Real-time price updates

### 4. Leverage Suggestions
When queries return no results, the system provides suggestions:
- Alternative product names
- Similar categories
- Different platforms to try
- Query refinement tips

## Sample Query Workflows

### Workflow 1: Weekly Grocery Shopping
```
1. "Find best vegetable deals this week"
2. "Compare fruit prices across all platforms"
3. "Show dairy discounts above 20%"
4. "Optimize ₹1500 grocery budget"
5. "Find fastest delivery for selected items"
```

### Workflow 2: Price Monitoring
```
1. "Show onion price trends"
2. "Compare today's prices with yesterday"
3. "Find platforms with price drops"
4. "Set alerts for price changes"
```

### Workflow 3: Deal Hunting
```
1. "Show all deals above 40% discount"
2. "Find flash sales ending today"
3. "Compare bulk purchase offers"
4. "Find combo deal savings"
```

## Integration with Advanced Features

### Using with Advanced Query Endpoint
For more control, use the advanced endpoint with natural language:

```json
{
  "query": "Find cheapest vegetables",
  "page": 1,
  "page_size": 20,
  "sampling_method": "top_n",
  "result_format": "comparison"
}
```

### Combining with Product Comparison
1. Start with natural language query
2. Use specific product IDs for detailed comparison
3. Apply filters for refined results

### Leveraging Caching
- Repeated similar queries benefit from caching
- Results are cached for 5 minutes
- Modify queries slightly to get fresh data when needed

---

*This guide covers the most common query patterns. The system continuously learns and improves its natural language understanding capabilities.*