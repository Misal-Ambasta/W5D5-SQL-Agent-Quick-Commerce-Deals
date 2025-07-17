# LangChain Integration and Query Processing Guide

## Overview

The Quick Commerce Deals platform leverages LangChain v0.3+ to convert natural language queries into optimized SQL operations. This guide provides technical details about the integration architecture, query processing pipeline, and customization options.

## Architecture Overview

### Core Components

```mermaid
graph TB
    subgraph "LangChain Integration Layer"
        NLQ[Natural Language Query]
        AGENT[Custom SQL Agent]
        TOOLKIT[SQL Database Toolkit]
        LLM[ChatOpenAI LLM]
    end
    
    subgraph "Custom Extensions"
        SI[Semantic Indexer]
        QP[Query Planner]
        MSP[Multi-Step Processor]
        RH[Result Handler]
    end
    
    subgraph "Database Layer"
        DB[(PostgreSQL)]
        SCHEMA[Schema Cache]
        POOL[Connection Pool]
    end
    
    NLQ --> AGENT
    AGENT --> TOOLKIT
    TOOLKIT --> LLM
    AGENT --> SI
    AGENT --> QP
    AGENT --> MSP
    SI --> SCHEMA
    QP --> DB
    MSP --> RH
    RH --> DB
```

## LangChain v0.3+ Integration

### 1. Core SQL Agent Implementation

```python
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain.agents import AgentType

class CustomSQLAgent:
    def __init__(self, database_uri: str, openai_api_key: str):
        # Initialize database connection
        self.db = SQLDatabase.from_uri(
            database_uri,
            include_tables=None,  # Include all tables
            sample_rows_in_table_info=3,
            custom_table_info=self._get_custom_table_info()
        )
        
        # Initialize LLM with optimized settings
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            openai_api_key=openai_api_key,
            max_tokens=1000
        )
        
        # Create SQL toolkit
        self.toolkit = SQLDatabaseToolkit(
            db=self.db, 
            llm=self.llm
        )
        
        # Create agent with custom configuration
        self.agent = create_sql_agent(
            llm=self.llm,
            toolkit=self.toolkit,
            verbose=True,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            handle_parsing_errors=True,
            max_iterations=5,
            early_stopping_method="generate"
        )
        
        # Initialize custom extensions
        self.semantic_indexer = SemanticTableIndexer(self.db)
        self.query_planner = QueryPlanner(self.db)
        self.multi_step_processor = MultiStepQueryProcessor(self.db, self.llm)
```

### 2. Custom Table Information

The system provides enhanced table information to the LLM for better query generation:

```python
def _get_custom_table_info(self) -> Dict[str, str]:
    """Provide custom table descriptions for better LLM understanding"""
    return {
        "products": """
        Core product catalog with comprehensive product information.
        Key columns: id, name, brand_id, category_id, description, pack_size, is_organic
        Relationships: Links to product_brands, product_categories, current_prices
        Use for: Product searches, filtering by attributes
        """,
        
        "current_prices": """
        Real-time pricing data across all platforms.
        Key columns: product_id, platform_id, price, original_price, discount_percentage, is_available
        Relationships: Links to products and platforms
        Use for: Price comparisons, discount calculations, availability checks
        """,
        
        "platforms": """
        Quick commerce platform information.
        Key columns: id, name, is_active
        Common values: Blinkit, Zepto, Instamart, BigBasket Now
        Use for: Platform-specific queries and comparisons
        """,
        
        "discounts": """
        Active discount and promotional information.
        Key columns: discount_percentage, discount_code, platform_id, product_id, category_id
        Use for: Finding deals, discount-based queries
        """
    }
```

## Semantic Table Indexer

### Purpose
The Semantic Table Indexer intelligently selects relevant tables from the 50+ available tables based on query context, reducing query complexity and improving performance.

### Implementation

```python
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict
import pickle

class SemanticTableIndexer:
    def __init__(self, database):
        self.db = database
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.table_embeddings = {}
        self.column_embeddings = {}
        self.table_descriptions = {}
        self._build_semantic_index()
    
    def _build_semantic_index(self):
        """Build semantic embeddings for all tables and columns"""
        tables = self.db.get_usable_table_names()
        
        for table in tables:
            # Get table schema information
            table_info = self.db.get_table_info_no_throw([table])
            
            # Create comprehensive description
            description = self._create_table_description(table, table_info)
            self.table_descriptions[table] = description
            
            # Generate embedding
            embedding = self.model.encode(description)
            self.table_embeddings[table] = embedding
            
            # Generate column embeddings
            columns = self._extract_columns(table_info)
            for column in columns:
                col_key = f"{table}.{column['name']}"
                col_description = f"{column['name']} {column.get('type', '')} {column.get('description', '')}"
                self.column_embeddings[col_key] = self.model.encode(col_description)
    
    def _create_table_description(self, table_name: str, table_info: str) -> str:
        """Create comprehensive table description for embedding"""
        # Extract meaningful information from table schema
        description_parts = [table_name.replace('_', ' ')]
        
        # Add domain-specific context
        if 'price' in table_name:
            description_parts.append("pricing cost money discount savings")
        elif 'product' in table_name:
            description_parts.append("items goods merchandise catalog inventory")
        elif 'platform' in table_name:
            description_parts.append("app service provider blinkit zepto instamart")
        elif 'discount' in table_name:
            description_parts.append("deals offers promotions savings percentage")
        elif 'category' in table_name:
            description_parts.append("classification type group vegetables fruits dairy")
        
        # Add table schema information
        description_parts.append(table_info)
        
        return " ".join(description_parts)
    
    async def get_relevant_tables(self, query: str, top_k: int = 10) -> List[str]:
        """Return most relevant tables based on semantic similarity"""
        query_embedding = self.model.encode(query)
        
        # Calculate similarities
        similarities = {}
        for table, embedding in self.table_embeddings.items():
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            similarities[table] = similarity
        
        # Sort by similarity and return top-k
        sorted_tables = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
        relevant_tables = [table for table, score in sorted_tables[:top_k] if score > 0.3]
        
        # Always include core tables for basic functionality
        core_tables = ['products', 'current_prices', 'platforms']
        for table in core_tables:
            if table not in relevant_tables:
                relevant_tables.append(table)
        
        return relevant_tables[:top_k]
```

## Query Planner and Optimizer

### Purpose
The Query Planner determines optimal join paths and execution strategies for multi-table queries.

### Implementation

```python
import networkx as nx
from typing import List, Dict, Tuple

class QueryPlanner:
    def __init__(self, database):
        self.db = database
        self.join_graph = self._build_join_graph()
        self.table_stats = self._collect_table_statistics()
    
    def _build_join_graph(self) -> nx.Graph:
        """Build graph of table relationships for optimal join planning"""
        G = nx.Graph()
        
        # Add nodes for all tables
        tables = self.db.get_usable_table_names()
        G.add_nodes_from(tables)
        
        # Add edges based on foreign key relationships
        relationships = self._discover_relationships()
        for rel in relationships:
            # Weight edges based on expected join cost
            weight = self._calculate_join_cost(rel['from_table'], rel['to_table'])
            G.add_edge(rel['from_table'], rel['to_table'], weight=weight)
        
        return G
    
    def _discover_relationships(self) -> List[Dict]:
        """Discover foreign key relationships between tables"""
        relationships = []
        
        # Define known relationships in the schema
        known_relationships = [
            {'from_table': 'current_prices', 'to_table': 'products', 'on': 'product_id'},
            {'from_table': 'current_prices', 'to_table': 'platforms', 'on': 'platform_id'},
            {'from_table': 'products', 'to_table': 'product_brands', 'on': 'brand_id'},
            {'from_table': 'products', 'to_table': 'product_categories', 'on': 'category_id'},
            {'from_table': 'discounts', 'to_table': 'platforms', 'on': 'platform_id'},
            {'from_table': 'discounts', 'to_table': 'products', 'on': 'product_id'},
            {'from_table': 'discounts', 'to_table': 'product_categories', 'on': 'category_id'},
        ]
        
        return known_relationships
    
    def _calculate_join_cost(self, table1: str, table2: str) -> float:
        """Calculate estimated cost of joining two tables"""
        # Simple heuristic based on table sizes
        size1 = self.table_stats.get(table1, {}).get('row_count', 1000)
        size2 = self.table_stats.get(table2, {}).get('row_count', 1000)
        
        # Cost is roughly proportional to the product of table sizes
        return (size1 * size2) / 1000000  # Normalize
    
    async def create_execution_plan(self, query: str, relevant_tables: List[str]) -> Dict:
        """Create optimized execution plan for multi-table queries"""
        if len(relevant_tables) <= 1:
            return {
                'tables': relevant_tables,
                'join_order': relevant_tables,
                'estimated_cost': 1.0,
                'optimization_notes': ['Single table query - no joins needed']
            }
        
        # Find optimal join order using shortest path
        join_order = self._find_optimal_join_order(relevant_tables)
        
        # Estimate total execution cost
        estimated_cost = self._estimate_query_cost(join_order)
        
        # Generate optimization suggestions
        optimization_notes = self._generate_optimization_notes(join_order, query)
        
        return {
            'tables': relevant_tables,
            'join_order': join_order,
            'estimated_cost': estimated_cost,
            'optimization_notes': optimization_notes,
            'relevant_tables': relevant_tables
        }
    
    def _find_optimal_join_order(self, tables: List[str]) -> List[str]:
        """Find optimal order for joining tables"""
        if len(tables) <= 2:
            return tables
        
        # Start with the most connected table (usually products or current_prices)
        connectivity = {}
        for table in tables:
            connectivity[table] = len([n for n in self.join_graph.neighbors(table) if n in tables])
        
        # Sort by connectivity (most connected first)
        sorted_tables = sorted(tables, key=lambda t: connectivity[t], reverse=True)
        
        return sorted_tables
```

## Multi-Step Query Processing

### Purpose
Breaks complex queries into logical steps with validation at each stage.

### Implementation

```python
from dataclasses import dataclass
from typing import List, Optional, Any
import asyncio

@dataclass
class QueryStep:
    step_number: int
    description: str
    sql_query: str
    expected_result_type: str
    validation_rules: List[str]
    depends_on: List[int]

@dataclass
class ExecutionResult:
    success: bool
    data: Any
    error_message: Optional[str]
    execution_time: float
    rows_affected: int

class MultiStepQueryProcessor:
    def __init__(self, database, llm):
        self.db = database
        self.llm = llm
        self.step_cache = {}
    
    async def create_execution_plan(self, query: str, context: Dict) -> Dict:
        """Create multi-step execution plan for complex queries"""
        
        # Analyze query complexity
        complexity_analysis = await self._analyze_query_complexity(query)
        
        if complexity_analysis['complexity_score'] < 3:
            # Simple query - single step
            return {
                'steps': [
                    QueryStep(
                        step_number=1,
                        description=f"Execute simple query: {query}",
                        sql_query="",  # Will be generated by LangChain
                        expected_result_type="product_list",
                        validation_rules=["results_not_empty", "valid_prices"],
                        depends_on=[]
                    )
                ],
                'total_steps': 1,
                'estimated_time': 2.0,
                'relevant_tables': context.get('relevant_tables', [])
            }
        
        # Complex query - break into steps
        steps = await self._break_into_steps(query, complexity_analysis)
        
        return {
            'steps': steps,
            'total_steps': len(steps),
            'estimated_time': len(steps) * 1.5,
            'relevant_tables': context.get('relevant_tables', [])
        }
    
    async def execute_plan(self, execution_plan: Dict) -> ExecutionResult:
        """Execute multi-step plan with validation"""
        steps = execution_plan['steps']
        step_results = {}
        
        try:
            for step in steps:
                # Check dependencies
                if not self._check_dependencies(step, step_results):
                    return ExecutionResult(
                        success=False,
                        data=None,
                        error_message=f"Step {step.step_number} dependencies not met",
                        execution_time=0,
                        rows_affected=0
                    )
                
                # Execute step
                step_result = await self._execute_step(step, step_results)
                
                if not step_result.success:
                    return ExecutionResult(
                        success=False,
                        data=None,
                        error_message=f"Step {step.step_number} failed: {step_result.error_message}",
                        execution_time=step_result.execution_time,
                        rows_affected=0
                    )
                
                step_results[step.step_number] = step_result
            
            # Combine results from all steps
            final_result = self._combine_step_results(step_results)
            
            return ExecutionResult(
                success=True,
                data=final_result,
                error_message=None,
                execution_time=sum(r.execution_time for r in step_results.values()),
                rows_affected=sum(r.rows_affected for r in step_results.values())
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                data=None,
                error_message=str(e),
                execution_time=0,
                rows_affected=0
            )
    
    async def _analyze_query_complexity(self, query: str) -> Dict:
        """Analyze query complexity to determine processing approach"""
        complexity_indicators = {
            'multiple_platforms': len([p for p in ['blinkit', 'zepto', 'instamart', 'bigbasket'] if p in query.lower()]),
            'comparison_words': len([w for w in ['compare', 'vs', 'versus', 'between'] if w in query.lower()]),
            'aggregation_words': len([w for w in ['cheapest', 'best', 'maximum', 'minimum', 'average'] if w in query.lower()]),
            'filter_words': len([w for w in ['discount', 'deal', 'offer', 'under', 'above', 'between'] if w in query.lower()]),
            'budget_words': len([w for w in ['₹', 'rs', 'rupees', 'budget', 'spend'] if w in query.lower()])
        }
        
        complexity_score = sum(complexity_indicators.values())
        
        return {
            'complexity_score': complexity_score,
            'indicators': complexity_indicators,
            'requires_multi_step': complexity_score >= 3
        }
    
    async def _break_into_steps(self, query: str, analysis: Dict) -> List[QueryStep]:
        """Break complex query into logical steps"""
        steps = []
        
        # Step 1: Always start with product identification
        steps.append(QueryStep(
            step_number=1,
            description="Identify relevant products",
            sql_query="",
            expected_result_type="product_list",
            validation_rules=["results_not_empty"],
            depends_on=[]
        ))
        
        # Step 2: Get pricing information
        steps.append(QueryStep(
            step_number=2,
            description="Retrieve current pricing data",
            sql_query="",
            expected_result_type="price_list",
            validation_rules=["valid_prices", "current_data"],
            depends_on=[1]
        ))
        
        # Additional steps based on query complexity
        if analysis['indicators']['comparison_words'] > 0:
            steps.append(QueryStep(
                step_number=len(steps) + 1,
                description="Perform platform comparison",
                sql_query="",
                expected_result_type="comparison_result",
                validation_rules=["multiple_platforms", "price_differences"],
                depends_on=[2]
            ))
        
        if analysis['indicators']['budget_words'] > 0:
            steps.append(QueryStep(
                step_number=len(steps) + 1,
                description="Optimize for budget constraints",
                sql_query="",
                expected_result_type="optimized_list",
                validation_rules=["within_budget", "maximum_value"],
                depends_on=[2]
            ))
        
        return steps
```

## Error Handling and Recovery

### Query Processing Errors

```python
class QueryProcessingError(Exception):
    def __init__(self, message: str, query: str, suggestions: List[str] = None):
        self.message = message
        self.query = query
        self.suggestions = suggestions or []
        super().__init__(self.message)

class LangChainErrorHandler:
    @staticmethod
    def handle_sql_generation_error(error: Exception, query: str) -> Dict:
        """Handle SQL generation errors from LangChain"""
        suggestions = []
        
        if "table" in str(error).lower():
            suggestions.extend([
                "Try using more specific product names",
                "Check if the product category exists",
                "Use platform names like Blinkit, Zepto, Instamart"
            ])
        
        if "column" in str(error).lower():
            suggestions.extend([
                "Rephrase your query with different terms",
                "Try asking for price, discount, or availability information"
            ])
        
        return {
            "error_type": "SQL Generation Error",
            "original_error": str(error),
            "query": query,
            "suggestions": suggestions,
            "fallback_available": True
        }
    
    @staticmethod
    def handle_execution_error(error: Exception, sql_query: str) -> Dict:
        """Handle SQL execution errors"""
        suggestions = [
            "The query might be too complex - try breaking it down",
            "Check if all specified platforms and products exist",
            "Try a simpler version of your query first"
        ]
        
        return {
            "error_type": "Query Execution Error",
            "original_error": str(error),
            "sql_query": sql_query,
            "suggestions": suggestions,
            "fallback_available": True
        }
```

## Performance Optimization

### 1. Query Caching

```python
import hashlib
import json
from typing import Optional

class QueryCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes
    
    def _generate_cache_key(self, query: str, context: Dict) -> str:
        """Generate unique cache key for query and context"""
        cache_data = {
            'query': query.lower().strip(),
            'context': context
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return f"query_cache:{hashlib.md5(cache_string.encode()).hexdigest()}"
    
    async def get_cached_result(self, query: str, context: Dict) -> Optional[Dict]:
        """Retrieve cached query result"""
        cache_key = self._generate_cache_key(query, context)
        cached_data = await self.redis.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        return None
    
    async def cache_result(self, query: str, context: Dict, result: Dict, ttl: int = None):
        """Cache query result"""
        cache_key = self._generate_cache_key(query, context)
        cache_ttl = ttl or self.default_ttl
        
        await self.redis.setex(
            cache_key,
            cache_ttl,
            json.dumps(result, default=str)
        )
```

### 2. Connection Pooling

```python
from sqlalchemy.pool import QueuePool

# Optimized database configuration
DATABASE_CONFIG = {
    'poolclass': QueuePool,
    'pool_size': 20,
    'max_overflow': 30,
    'pool_pre_ping': True,
    'pool_recycle': 3600,
    'echo': False
}
```

## Monitoring and Debugging

### Query Performance Monitoring

```python
import time
import logging
from functools import wraps

def monitor_query_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log successful query
            logging.info(f"Query executed successfully", extra={
                'function': func.__name__,
                'execution_time': execution_time,
                'success': True
            })
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Log failed query
            logging.error(f"Query execution failed", extra={
                'function': func.__name__,
                'execution_time': execution_time,
                'error': str(e),
                'success': False
            })
            
            raise
    
    return wrapper
```

## Configuration and Customization

### Environment Variables

```bash
# LangChain Configuration
OPENAI_API_KEY=your_openai_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langchain_api_key
LANGCHAIN_PROJECT=quick-commerce-deals

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/quickcommerce
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Cache Configuration
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=300

# Query Processing Configuration
MAX_QUERY_COMPLEXITY=10
SEMANTIC_SIMILARITY_THRESHOLD=0.3
MAX_RELEVANT_TABLES=10
```

### Custom Configuration

```python
from pydantic import BaseSettings

class LangChainSettings(BaseSettings):
    openai_api_key: str
    model_name: str = "gpt-3.5-turbo"
    temperature: float = 0.0
    max_tokens: int = 1000
    max_iterations: int = 5
    
    # Semantic indexing settings
    similarity_threshold: float = 0.3
    max_relevant_tables: int = 10
    
    # Query processing settings
    max_query_complexity: int = 10
    enable_multi_step: bool = True
    cache_ttl: int = 300
    
    class Config:
        env_prefix = "LANGCHAIN_"
```

## Best Practices

### 1. Query Optimization
- Use semantic table selection to reduce query complexity
- Implement proper caching strategies
- Monitor query performance and optimize slow queries
- Use connection pooling for database efficiency

### 2. Error Handling
- Provide meaningful error messages with suggestions
- Implement fallback mechanisms for failed queries
- Log errors for debugging and improvement
- Use retry logic for transient failures

### 3. Security
- Validate and sanitize all user inputs
- Use parameterized queries to prevent SQL injection
- Implement rate limiting to prevent abuse
- Monitor for suspicious query patterns

### 4. Monitoring
- Track query performance metrics
- Monitor LangChain API usage and costs
- Log query patterns for system improvement
- Set up alerts for system issues

---

*This guide provides comprehensive technical details for working with the LangChain integration. For implementation examples and troubleshooting, refer to the source code and error handling documentation.*