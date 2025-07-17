"""
LangChain SQL Agent implementation using Google Gemini
"""
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.agents.agent_types import AgentType
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import (
    QueryProcessingError,
    DatabaseError,
    InvalidQueryError,
    ConfigurationError
)
from app.services.semantic_indexer import get_semantic_indexer
from app.services.query_planner import get_query_planner

logger = logging.getLogger(__name__)


class CustomSQLAgent:
    """
    Custom SQL Agent using LangChain v0.3+ with Google Gemini
    """
    
    def __init__(self):
        self.llm = None
        self.db = None
        self.toolkit = None
        self.agent = None
        self.schema_info = {}
        self.semantic_indexer = None
        self.query_planner = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the SQL agent components"""
        try:
            # Validate Google API key
            if not settings.GOOGLE_API_KEY or settings.GOOGLE_API_KEY == "your-google-api-key-here":
                raise ConfigurationError(
                    "Google API key not configured",
                    config_key="GOOGLE_API_KEY",
                    suggestions=[
                        "Set GOOGLE_API_KEY environment variable",
                        "Update .env file with your Google API key",
                        "Get API key from Google AI Studio"
                    ]
                )
            
            # Initialize Gemini LLM
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0.1,  # Low temperature for more consistent SQL generation
                max_tokens=2048,
                timeout=30
            )
            
            # Initialize SQL Database connection
            self.db = SQLDatabase.from_uri(
                settings.database_url,
                include_tables=None,  # Include all tables
                sample_rows_in_table_info=3,  # Include sample data for context
                custom_table_info=self._get_custom_table_info()
            )
            
            # Create SQL Database Toolkit
            self.toolkit = SQLDatabaseToolkit(
                db=self.db,
                llm=self.llm
            )
            
            # Create the SQL agent with custom system message
            self.agent = create_sql_agent(
                llm=self.llm,
                toolkit=self.toolkit,
                agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                max_iterations=5,
                max_execution_time=60,
                early_stopping_method="generate",
                handle_parsing_errors=True,
                agent_executor_kwargs={
                    "return_intermediate_steps": True
                }
            )
            
            # Load schema information for better context
            self._load_schema_info()
            
            # Initialize semantic indexer for intelligent table selection
            try:
                self.semantic_indexer = get_semantic_indexer()
                logger.info("Semantic indexer integrated successfully")
            except Exception as e:
                logger.warning(f"Could not initialize semantic indexer: {str(e)}")
                self.semantic_indexer = None
            
            # Initialize query planner for optimal join path determination
            try:
                self.query_planner = get_query_planner()
                logger.info("Query planner integrated successfully")
            except Exception as e:
                logger.warning(f"Could not initialize query planner: {str(e)}")
                self.query_planner = None
            
            logger.info("SQL Agent initialized successfully with Gemini model")
            
        except Exception as e:
            logger.error(f"Failed to initialize SQL Agent: {str(e)}")
            raise ConfigurationError(f"SQL Agent initialization failed: {str(e)}")
    
    def _get_custom_table_info(self) -> Dict[str, str]:
        """Get custom table information for better context"""
        return {
            "platforms": "Contains quick commerce platforms like Blinkit, Zepto, Instamart, BigBasket",
            "products": "Contains product information with names, descriptions, categories, brands",
            "current_prices": "Contains current pricing data for products across platforms",
            "price_history": "Historical pricing data for trend analysis",
            "discounts": "Active discounts and promotional offers",
            "promotional_campaigns": "Marketing campaigns and special offers",
            "product_categories": "Product categorization (fruits, vegetables, dairy, etc.)",
            "product_brands": "Brand information for products",
            "inventory_levels": "Current stock levels across platforms",
            "availability_status": "Product availability status"
        }
    
    def _load_schema_info(self):
        """Load comprehensive schema information"""
        try:
            inspector = inspect(engine)
            
            # Get all table names
            table_names = inspector.get_table_names()
            
            for table_name in table_names:
                # Get column information
                columns = inspector.get_columns(table_name)
                
                # Get foreign keys
                foreign_keys = inspector.get_foreign_keys(table_name)
                
                # Get indexes
                indexes = inspector.get_indexes(table_name)
                
                self.schema_info[table_name] = {
                    "columns": columns,
                    "foreign_keys": foreign_keys,
                    "indexes": indexes
                }
            
            logger.info(f"Loaded schema information for {len(table_names)} tables")
            
        except Exception as e:
            logger.warning(f"Could not load complete schema info: {str(e)}")
    
    def _create_system_prompt(self) -> str:
        """Create a comprehensive system prompt for the SQL agent"""
        return """You are an expert SQL agent for a Quick Commerce Deals platform that helps users find product prices, deals, and comparisons across multiple platforms.

IMPORTANT GUIDELINES:
1. Always use proper SQL syntax for PostgreSQL
2. Use table aliases for better readability
3. Always include proper JOIN conditions
4. Filter for active/available products and platforms (is_active = true, is_available = true)
5. Use ILIKE for case-insensitive text searches
6. Always limit results to prevent large datasets (use LIMIT)
7. Include relevant columns like product names, platform names, prices, discounts
8. For price comparisons, order by price ASC to show cheapest first
9. For discount queries, order by discount_percentage DESC
10. Always validate that the generated SQL is safe and doesn't modify data

KEY TABLES AND RELATIONSHIPS:
- platforms: id, name, is_active
- products: id, name, description, category_id, brand_id, is_active
- current_prices: product_id, platform_id, price, original_price, discount_percentage, is_available
- product_categories: id, name
- product_brands: id, name
- discounts: id, title, platform_id, discount_percentage, is_active
- promotional_campaigns: id, campaign_name, platform_id, is_active

COMMON QUERY PATTERNS:
1. "Cheapest [product]" → Find lowest price across platforms
2. "Discounts on [platform]" → Find active discounts for specific platform
3. "Compare [product] prices" → Show prices across all platforms
4. "[X]% discount" → Find products with specific discount percentage

SAMPLE QUERIES:
- "Which app has cheapest onions?" → Compare onion prices across platforms
- "30% discount on Blinkit" → Find products with 30%+ discount on Blinkit
- "Compare apple prices" → Show apple prices on all platforms

Always explain your SQL query and provide helpful insights about the results."""

    async def process_query(
        self, 
        query: str, 
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process natural language query and return structured results
        
        Args:
            query: Natural language query
            user_context: Optional user context for personalization
            
        Returns:
            Dictionary with query results, SQL, and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing query: {query}")
            
            # Validate agent is initialized
            if not self.agent:
                raise QueryProcessingError("SQL Agent not properly initialized")
            
            # Create enhanced prompt with context
            enhanced_query = await self._enhance_query_with_context(query, user_context)
            
            # Execute the query using the agent
            result = await self._execute_agent_query(enhanced_query)
            
            # Process and format the results
            formatted_result = self._format_agent_result(result, query)
            
            execution_time = time.time() - start_time
            formatted_result["execution_time"] = execution_time
            
            logger.info(f"Query processed successfully in {execution_time:.2f}s")
            return formatted_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query processing failed after {execution_time:.2f}s: {str(e)}")
            
            if isinstance(e, (QueryProcessingError, DatabaseError, InvalidQueryError)):
                raise e
            else:
                raise QueryProcessingError(
                    f"Failed to process query: {str(e)}", 
                    query=query
                )
    
    async def _enhance_query_with_context(
        self, 
        query: str, 
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Enhance query with additional context and semantic table selection"""
        
        enhanced_query = f"""
Query: {query}

Context Information:
- This is a quick commerce platform comparison system
- Focus on finding the best deals and prices for users
- Include platform names (Blinkit, Zepto, Instamart, BigBasket) in results
- Show prices in Indian Rupees (₹)
- Prioritize available products and active platforms
"""
        
        # Add semantic table selection and query planning if available
        if self.semantic_indexer:
            try:
                relevant_tables = await self.semantic_indexer.get_relevant_tables(query, top_k=8)
                if relevant_tables:
                    table_names = [table for table, score in relevant_tables]
                    enhanced_query += f"\nMost Relevant Tables (focus on these): {', '.join(table_names)}\n"
                    
                    # Use query planner to create execution plan
                    if self.query_planner and len(table_names) > 1:
                        try:
                            execution_plan = await self.query_planner.create_execution_plan(
                                query, table_names, user_context
                            )
                            
                            # Add execution plan information to the query
                            enhanced_query += f"\nQuery Execution Plan:\n"
                            enhanced_query += f"- Optimal join order: {' -> '.join(execution_plan.join_order)}\n"
                            enhanced_query += f"- Query complexity: {execution_plan.complexity.value}\n"
                            enhanced_query += f"- Estimated execution time: {execution_plan.execution_time_estimate}s\n"
                            
                            # Add join path suggestions
                            if execution_plan.join_paths:
                                enhanced_query += "\nOptimal Join Paths:\n"
                                for join_path in execution_plan.join_paths[:3]:  # Limit to top 3
                                    enhanced_query += f"- {join_path.condition} ({join_path.join_type.value})\n"
                            
                            # Add optimization suggestions
                            if execution_plan.optimization_suggestions:
                                enhanced_query += "\nOptimization Suggestions:\n"
                                for suggestion in execution_plan.optimization_suggestions[:3]:
                                    enhanced_query += f"- {suggestion}\n"
                            
                            logger.info(f"Query planner created execution plan with {len(execution_plan.join_paths)} joins")
                            
                        except Exception as e:
                            logger.warning(f"Could not create execution plan: {str(e)}")
                            # Fallback to basic join suggestions
                            join_suggestions = self.semantic_indexer.get_join_suggestions(table_names[:5])
                            if join_suggestions:
                                enhanced_query += "\nSuggested Table Joins:\n"
                                for join in join_suggestions[:3]:  # Limit to top 3 joins
                                    enhanced_query += f"- {join['condition']} ({join['join_type']})\n"
                    else:
                        # Fallback to basic join suggestions for single table or no planner
                        join_suggestions = self.semantic_indexer.get_join_suggestions(table_names[:5])
                        if join_suggestions:
                            enhanced_query += "\nSuggested Table Joins:\n"
                            for join in join_suggestions[:3]:  # Limit to top 3 joins
                                enhanced_query += f"- {join['condition']} ({join['join_type']})\n"
                    
                    logger.info(f"Semantic indexer identified {len(relevant_tables)} relevant tables for query")
                else:
                    logger.warning("Semantic indexer found no relevant tables")
            except Exception as e:
                logger.warning(f"Could not get semantic table suggestions: {str(e)}")
        
        if user_context:
            if user_context.get("location"):
                enhanced_query += f"- User location: {user_context['location']}\n"
            if user_context.get("preferences"):
                enhanced_query += f"- User preferences: {user_context['preferences']}\n"
        
        enhanced_query += f"\nPlease generate appropriate SQL query and execute it to answer: {query}"
        
        return enhanced_query
    
    async def _execute_agent_query(self, query: str) -> Dict[str, Any]:
        """Execute query using the LangChain agent"""
        try:
            # Use the agent to process the query
            result = self.agent.invoke({"input": query})
            
            return result
            
        except Exception as e:
            logger.error(f"Agent execution failed: {str(e)}")
            
            # Check for specific error types
            if "timeout" in str(e).lower():
                raise QueryProcessingError("Query execution timed out", query=query)
            elif "syntax error" in str(e).lower():
                raise InvalidQueryError("Generated SQL has syntax errors", query=query)
            elif "permission denied" in str(e).lower():
                raise DatabaseError("Database permission denied", operation="query_execution")
            else:
                raise QueryProcessingError(f"Agent execution failed: {str(e)}", query=query)
    
    def _format_agent_result(self, result: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """Format agent result into standardized response"""
        
        try:
            # Extract the main output
            output = result.get("output", "")
            
            # Extract intermediate steps for SQL query
            intermediate_steps = result.get("intermediate_steps", [])
            
            # Try to extract SQL query from intermediate steps
            sql_query = self._extract_sql_from_steps(intermediate_steps)
            
            # Parse the output to extract structured data
            structured_data = self._parse_agent_output(output)
            
            return {
                "query": original_query,
                "sql_query": sql_query,
                "results": structured_data,
                "raw_output": output,
                "success": True,
                "error": None,
                "suggestions": self._generate_suggestions(original_query, structured_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to format agent result: {str(e)}")
            return {
                "query": original_query,
                "sql_query": None,
                "results": [],
                "raw_output": str(result),
                "success": False,
                "error": str(e),
                "suggestions": [
                    "Try rephrasing your query",
                    "Use more specific product names",
                    "Check spelling and grammar"
                ]
            }
    
    def _extract_sql_from_steps(self, intermediate_steps: List[Tuple]) -> Optional[str]:
        """Extract SQL query from intermediate steps"""
        try:
            for step in intermediate_steps:
                if len(step) >= 2:
                    action, observation = step[0], step[1]
                    
                    # Look for SQL query in action
                    if hasattr(action, 'tool_input') and isinstance(action.tool_input, str):
                        if "SELECT" in action.tool_input.upper():
                            return action.tool_input.strip()
                    
                    # Look for SQL query in observation
                    if isinstance(observation, str) and "SELECT" in observation.upper():
                        # Extract SQL from observation
                        lines = observation.split('\n')
                        for line in lines:
                            if "SELECT" in line.upper():
                                return line.strip()
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not extract SQL from steps: {str(e)}")
            return None
    
    def _parse_agent_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse agent output to extract structured data"""
        try:
            # This is a simplified parser - in production, you might want more sophisticated parsing
            results = []
            
            # Look for table-like data in the output
            lines = output.split('\n')
            
            for line in lines:
                line = line.strip()
                if line and '|' in line and not line.startswith('|--'):
                    # This looks like table data
                    parts = [part.strip() for part in line.split('|') if part.strip()]
                    if len(parts) >= 3:  # Assuming at least product, platform, price
                        result = {
                            "product_name": parts[0] if len(parts) > 0 else "",
                            "platform_name": parts[1] if len(parts) > 1 else "",
                            "price": self._extract_price(parts[2]) if len(parts) > 2 else 0.0,
                            "additional_info": parts[3:] if len(parts) > 3 else []
                        }
                        results.append(result)
            
            return results
            
        except Exception as e:
            logger.warning(f"Could not parse agent output: {str(e)}")
            return []
    
    def _extract_price(self, price_str: str) -> float:
        """Extract numeric price from string"""
        try:
            # Remove currency symbols and extract number
            import re
            numbers = re.findall(r'\d+\.?\d*', price_str)
            if numbers:
                return float(numbers[0])
            return 0.0
        except:
            return 0.0
    
    def _generate_suggestions(self, query: str, results: List[Dict[str, Any]]) -> List[str]:
        """Generate helpful suggestions based on query and results"""
        suggestions = []
        
        if not results:
            suggestions.extend([
                "Try using more general product names",
                "Check spelling of product or platform names",
                "Try queries like 'cheapest [product]' or 'compare [product] prices'"
            ])
        else:
            suggestions.extend([
                "Try comparing prices across different platforms",
                "Look for discount offers on specific platforms",
                "Check for seasonal price variations"
            ])
        
        # Add query-specific suggestions
        query_lower = query.lower()
        if "cheapest" in query_lower:
            suggestions.append("Consider checking for ongoing discounts on the cheapest option")
        elif "discount" in query_lower:
            suggestions.append("Check expiry dates for discount offers")
        elif "compare" in query_lower:
            suggestions.append("Consider delivery charges when comparing prices")
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get database schema information"""
        return {
            "tables": list(self.schema_info.keys()),
            "table_details": self.schema_info,
            "custom_info": self._get_custom_table_info()
        }
    
    def validate_sql_query(self, sql_query: str) -> Tuple[bool, Optional[str]]:
        """Validate SQL query for safety"""
        try:
            # Basic safety checks
            sql_upper = sql_query.upper().strip()
            
            # Check for dangerous operations
            dangerous_keywords = [
                "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", 
                "TRUNCATE", "EXEC", "EXECUTE", "GRANT", "REVOKE"
            ]
            
            for keyword in dangerous_keywords:
                if keyword in sql_upper:
                    return False, f"Dangerous SQL operation detected: {keyword}"
            
            # Must be a SELECT query
            if not sql_upper.startswith("SELECT"):
                return False, "Only SELECT queries are allowed"
            
            # Check for SQL injection patterns
            injection_patterns = [
                "--", "/*", "*/", ";", "UNION", "OR 1=1", "AND 1=1"
            ]
            
            for pattern in injection_patterns:
                if pattern in sql_upper:
                    return False, f"Potential SQL injection pattern detected: {pattern}"
            
            return True, None
            
        except Exception as e:
            return False, f"SQL validation error: {str(e)}"
    
    async def optimize_sql_with_planner(
        self, 
        sql_query: str, 
        original_query: str,
        relevant_tables: List[str]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Optimize SQL query using the query planner.
        
        Args:
            sql_query: Generated SQL query
            original_query: Original natural language query
            relevant_tables: List of relevant tables
            
        Returns:
            Tuple of (optimized_sql, optimization_info)
        """
        if not self.query_planner:
            return sql_query, {"optimization_applied": False, "reason": "Query planner not available"}
        
        try:
            # Create execution plan for the query
            execution_plan = await self.query_planner.create_execution_plan(
                original_query, relevant_tables
            )
            
            # Apply optimizations to the SQL query
            optimized_sql = self.query_planner.optimize_sql_query(sql_query, execution_plan)
            
            optimization_info = {
                "optimization_applied": True,
                "execution_plan": {
                    "complexity": execution_plan.complexity.value,
                    "estimated_cost": execution_plan.estimated_cost,
                    "execution_time_estimate": execution_plan.execution_time_estimate,
                    "join_paths_count": len(execution_plan.join_paths),
                    "optimization_suggestions": execution_plan.optimization_suggestions,
                    "index_recommendations": execution_plan.index_recommendations
                },
                "original_sql_length": len(sql_query),
                "optimized_sql_length": len(optimized_sql)
            }
            
            logger.info(f"SQL query optimized using query planner - complexity: {execution_plan.complexity.value}")
            
            return optimized_sql, optimization_info
            
        except Exception as e:
            logger.warning(f"Could not optimize SQL with query planner: {str(e)}")
            return sql_query, {
                "optimization_applied": False, 
                "reason": f"Optimization failed: {str(e)}"
            }
    
    async def analyze_query_performance(
        self, 
        sql_query: str, 
        execution_time: float
    ) -> Dict[str, Any]:
        """
        Analyze query performance using the query planner.
        
        Args:
            sql_query: Executed SQL query
            execution_time: Actual execution time in seconds
            
        Returns:
            Performance analysis with insights
        """
        if not self.query_planner:
            return {"analysis_available": False, "reason": "Query planner not available"}
        
        try:
            analysis = self.query_planner.analyze_query_performance(sql_query, execution_time)
            analysis["analysis_available"] = True
            
            logger.info(f"Query performance analyzed - rating: {analysis.get('performance_rating', 'unknown')}")
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Could not analyze query performance: {str(e)}")
            return {
                "analysis_available": False,
                "reason": f"Analysis failed: {str(e)}"
            }
    
    def get_query_planner_stats(self) -> Dict[str, Any]:
        """Get statistics about the query planner."""
        if not self.query_planner:
            return {"available": False}
        
        try:
            stats = self.query_planner.get_join_graph_stats()
            stats["available"] = True
            return stats
        except Exception as e:
            logger.warning(f"Could not get query planner stats: {str(e)}")
            return {"available": False, "error": str(e)}


# Global SQL agent instance
sql_agent = None

def get_sql_agent() -> CustomSQLAgent:
    """Get or create SQL agent instance"""
    global sql_agent
    
    if sql_agent is None:
        sql_agent = CustomSQLAgent()
    
    return sql_agent