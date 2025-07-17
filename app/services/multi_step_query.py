"""
Multi-step Query Generation and Validation for Quick Commerce Deals platform.
Breaks complex queries into logical validation steps with error recovery.
"""

import logging
import time
import json
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import asyncio
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.services.semantic_indexer import get_semantic_indexer
from app.services.query_planner import QueryPlanner

logger = logging.getLogger(__name__)


class QueryStepType(Enum):
    """Types of query steps"""
    TABLE_SELECTION = "table_selection"
    DATA_VALIDATION = "data_validation"
    JOIN_VALIDATION = "join_validation"
    FILTER_APPLICATION = "filter_application"
    AGGREGATION = "aggregation"
    RESULT_FORMATTING = "result_formatting"


class StepStatus(Enum):
    """Status of query step execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class QueryStep:
    """Represents a single step in multi-step query execution"""
    step_id: str
    step_type: QueryStepType
    description: str
    sql_fragment: str
    dependencies: List[str]  # IDs of steps this depends on
    validation_query: Optional[str] = None
    expected_result_type: str = "rows"  # "rows", "count", "exists"
    timeout_seconds: int = 30
    retry_count: int = 0
    max_retries: int = 2
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class QueryExecutionPlan:
    """Complete execution plan for multi-step query"""
    query_id: str
    original_query: str
    steps: List[QueryStep]
    total_steps: int
    estimated_execution_time: float
    complexity_score: int
    relevant_tables: List[str]
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.total_steps == 0:
            self.total_steps = len(self.steps)


@dataclass
class StepExecutionResult:
    """Result of executing a single query step"""
    step_id: str
    success: bool
    result: Any
    execution_time: float
    error_message: Optional[str] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


@dataclass
class MultiStepQueryResult:
    """Final result of multi-step query execution"""
    query_id: str
    original_query: str
    success: bool
    final_result: Any
    total_execution_time: float
    steps_executed: int
    steps_failed: int
    step_results: List[StepExecutionResult]
    error_recovery_applied: bool = False
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


class MultiStepQueryProcessor:
    """
    Processes complex queries by breaking them into logical validation steps.
    Provides error recovery and suggestion system for failed query steps.
    """
    
    def __init__(self):
        """Initialize the multi-step query processor."""
        self.semantic_indexer = get_semantic_indexer()
        self.query_planner = QueryPlanner()
        self.active_executions: Dict[str, QueryExecutionPlan] = {}
        
        # Step templates for common query patterns
        self.step_templates = self._initialize_step_templates()
        
        # Error recovery strategies
        self.recovery_strategies = self._initialize_recovery_strategies()
    
    def _initialize_step_templates(self) -> Dict[str, List[Dict]]:
        """Initialize templates for common query step patterns."""
        return {
            "price_comparison": [
                {
                    "step_type": QueryStepType.TABLE_SELECTION,
                    "description": "Select relevant tables for price comparison",
                    "validation_query": "SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ({tables})"
                },
                {
                    "step_type": QueryStepType.DATA_VALIDATION,
                    "description": "Validate product exists in database",
                    "validation_query": "SELECT COUNT(*) FROM products WHERE name ILIKE '%{product_name}%'"
                },
                {
                    "step_type": QueryStepType.JOIN_VALIDATION,
                    "description": "Validate table relationships for price data",
                    "validation_query": "SELECT COUNT(*) FROM products p JOIN current_prices cp ON p.id = cp.product_id LIMIT 1"
                },
                {
                    "step_type": QueryStepType.FILTER_APPLICATION,
                    "description": "Apply filters for active products and platforms",
                    "validation_query": "SELECT COUNT(*) FROM current_prices cp JOIN platforms pl ON cp.platform_id = pl.id WHERE pl.is_active = true"
                },
                {
                    "step_type": QueryStepType.RESULT_FORMATTING,
                    "description": "Format results for price comparison display",
                    "expected_result_type": "rows"
                }
            ],
            "discount_search": [
                {
                    "step_type": QueryStepType.TABLE_SELECTION,
                    "description": "Select tables for discount information",
                    "validation_query": "SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('current_prices', 'discounts', 'products', 'platforms')"
                },
                {
                    "step_type": QueryStepType.DATA_VALIDATION,
                    "description": "Validate discount data availability",
                    "validation_query": "SELECT COUNT(*) FROM current_prices WHERE discount_percentage > 0"
                },
                {
                    "step_type": QueryStepType.FILTER_APPLICATION,
                    "description": "Apply discount percentage filters",
                    "validation_query": "SELECT COUNT(*) FROM current_prices WHERE discount_percentage >= {min_discount}"
                },
                {
                    "step_type": QueryStepType.RESULT_FORMATTING,
                    "description": "Format discount results with savings calculation",
                    "expected_result_type": "rows"
                }
            ],
            "product_search": [
                {
                    "step_type": QueryStepType.TABLE_SELECTION,
                    "description": "Select product catalog tables",
                    "validation_query": "SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('products', 'product_categories', 'product_brands')"
                },
                {
                    "step_type": QueryStepType.DATA_VALIDATION,
                    "description": "Validate product search terms",
                    "validation_query": "SELECT COUNT(*) FROM products WHERE name ILIKE '%{search_term}%' OR description ILIKE '%{search_term}%'"
                },
                {
                    "step_type": QueryStepType.RESULT_FORMATTING,
                    "description": "Format product search results",
                    "expected_result_type": "rows"
                }
            ]
        }
    
    def _initialize_recovery_strategies(self) -> Dict[QueryStepType, List[str]]:
        """Initialize error recovery strategies for different step types."""
        return {
            QueryStepType.TABLE_SELECTION: [
                "Retry with alternative table names",
                "Use semantic similarity to find related tables",
                "Fall back to core tables (products, current_prices, platforms)"
            ],
            QueryStepType.DATA_VALIDATION: [
                "Broaden search criteria",
                "Try alternative product name variations",
                "Check for typos in product names"
            ],
            QueryStepType.JOIN_VALIDATION: [
                "Use LEFT JOIN instead of INNER JOIN",
                "Verify foreign key relationships",
                "Try alternative join paths"
            ],
            QueryStepType.FILTER_APPLICATION: [
                "Relax filter criteria",
                "Remove optional filters",
                "Use broader date ranges"
            ],
            QueryStepType.AGGREGATION: [
                "Use simpler aggregation functions",
                "Remove complex grouping",
                "Apply LIMIT to reduce result set"
            ],
            QueryStepType.RESULT_FORMATTING: [
                "Use basic column selection",
                "Remove complex formatting",
                "Return raw data if formatting fails"
            ]
        }
    
    async def create_execution_plan(
        self, 
        query: str, 
        query_context: Optional[Dict[str, Any]] = None
    ) -> QueryExecutionPlan:
        """
        Create a multi-step execution plan for a complex query.
        
        Args:
            query: Natural language query
            query_context: Additional context for query processing
            
        Returns:
            QueryExecutionPlan with ordered steps
        """
        logger.info(f"Creating execution plan for query: {query[:100]}...")
        
        try:
            # Generate unique query ID
            query_id = f"query_{int(time.time() * 1000)}"
            
            # Analyze query to determine pattern and complexity
            query_pattern = await self._analyze_query_pattern(query)
            complexity_score = self._calculate_complexity_score(query, query_context)
            
            # Get relevant tables using semantic indexer
            relevant_tables_with_scores = await self.semantic_indexer.get_relevant_tables(query, top_k=15)
            relevant_tables = [table for table, _ in relevant_tables_with_scores]
            
            # Create query execution plan using query planner
            planner_result = await self.query_planner.create_execution_plan(
                query, relevant_tables, query_context
            )
            
            # Generate steps based on query pattern and complexity
            steps = await self._generate_query_steps(
                query, query_pattern, relevant_tables, complexity_score, query_context
            )
            
            # Estimate total execution time
            estimated_time = sum(step.timeout_seconds * 0.1 for step in steps)  # Conservative estimate
            
            execution_plan = QueryExecutionPlan(
                query_id=query_id,
                original_query=query,
                steps=steps,
                total_steps=len(steps),
                estimated_execution_time=estimated_time,
                complexity_score=complexity_score,
                relevant_tables=relevant_tables
            )
            
            # Store active execution
            self.active_executions[query_id] = execution_plan
            
            logger.info(f"Created execution plan with {len(steps)} steps, complexity: {complexity_score}")
            return execution_plan
            
        except Exception as e:
            logger.error(f"Error creating execution plan: {str(e)}")
            raise
    
    async def _analyze_query_pattern(self, query: str) -> str:
        """Analyze query to determine the most appropriate pattern."""
        query_lower = query.lower()
        
        # Price comparison patterns
        if any(word in query_lower for word in ["cheapest", "compare", "price", "cost"]):
            return "price_comparison"
        
        # Discount search patterns
        if any(word in query_lower for word in ["discount", "%", "offer", "deal", "sale"]):
            return "discount_search"
        
        # Product search patterns
        if any(word in query_lower for word in ["find", "search", "show", "list"]):
            return "product_search"
        
        # Default to product search
        return "product_search"
    
    def _calculate_complexity_score(self, query: str, context: Optional[Dict] = None) -> int:
        """Calculate complexity score for the query (1-10 scale)."""
        score = 1
        query_lower = query.lower()
        
        # Length factor
        if len(query) > 100:
            score += 2
        elif len(query) > 50:
            score += 1
        
        # Multiple conditions
        condition_words = ["and", "or", "but", "with", "between", "compare"]
        score += sum(1 for word in condition_words if word in query_lower)
        
        # Specific platforms mentioned
        platforms = ["blinkit", "zepto", "instamart", "bigbasket", "swiggy"]
        score += len([p for p in platforms if p in query_lower])
        
        # Numerical constraints
        if any(char.isdigit() for char in query) or "%" in query:
            score += 1
        
        # Context complexity
        if context and len(context) > 3:
            score += 1
        
        return min(score, 10)  # Cap at 10
    
    async def _generate_query_steps(
        self,
        query: str,
        pattern: str,
        relevant_tables: List[str],
        complexity_score: int,
        context: Optional[Dict] = None
    ) -> List[QueryStep]:
        """Generate ordered query steps based on pattern and complexity."""
        steps = []
        
        # Get base template
        template_steps = self.step_templates.get(pattern, self.step_templates["product_search"])
        
        # Generate steps from template
        for i, template in enumerate(template_steps):
            step_id = f"step_{i+1}_{template['step_type'].value}"
            
            # Determine dependencies
            dependencies = []
            if i > 0:
                dependencies.append(f"step_{i}_{template_steps[i-1]['step_type'].value}")
            
            # Create SQL fragment based on step type and query
            sql_fragment = await self._generate_sql_fragment(
                template['step_type'], query, relevant_tables, context
            )
            
            # Create validation query
            validation_query = template.get('validation_query', '')
            if validation_query:
                validation_query = await self._customize_validation_query(
                    validation_query, query, context
                )
            
            step = QueryStep(
                step_id=step_id,
                step_type=template['step_type'],
                description=template['description'],
                sql_fragment=sql_fragment,
                dependencies=dependencies,
                validation_query=validation_query,
                expected_result_type=template.get('expected_result_type', 'rows'),
                timeout_seconds=min(30 + complexity_score * 5, 120)  # Scale timeout with complexity
            )
            
            steps.append(step)
        
        # Add complexity-specific steps
        if complexity_score >= 7:
            # Add result sampling step for complex queries
            sampling_step = QueryStep(
                step_id=f"step_{len(steps)+1}_sampling",
                step_type=QueryStepType.RESULT_FORMATTING,
                description="Apply statistical sampling for large result sets",
                sql_fragment="-- Statistical sampling will be applied",
                dependencies=[steps[-1].step_id] if steps else [],
                expected_result_type="rows",
                timeout_seconds=15
            )
            steps.append(sampling_step)
        
        return steps
    
    async def _generate_sql_fragment(
        self,
        step_type: QueryStepType,
        query: str,
        relevant_tables: List[str],
        context: Optional[Dict] = None
    ) -> str:
        """Generate SQL fragment for a specific step type."""
        
        if step_type == QueryStepType.TABLE_SELECTION:
            return f"-- Using tables: {', '.join(relevant_tables[:5])}"
        
        elif step_type == QueryStepType.DATA_VALIDATION:
            # Extract product name from query
            product_name = self._extract_product_name(query)
            return f"SELECT COUNT(*) FROM products WHERE name ILIKE '%{product_name}%'"
        
        elif step_type == QueryStepType.JOIN_VALIDATION:
            return """
            SELECT COUNT(*) FROM products p 
            JOIN current_prices cp ON p.id = cp.product_id 
            JOIN platforms pl ON cp.platform_id = pl.id 
            WHERE pl.is_active = true
            LIMIT 1
            """
        
        elif step_type == QueryStepType.FILTER_APPLICATION:
            filters = []
            if "discount" in query.lower():
                filters.append("cp.discount_percentage > 0")
            if "available" in query.lower():
                filters.append("cp.is_available = true")
            
            filter_clause = " AND ".join(filters) if filters else "1=1"
            return f"-- Apply filters: {filter_clause}"
        
        elif step_type == QueryStepType.AGGREGATION:
            if "cheapest" in query.lower():
                return "ORDER BY cp.price ASC"
            elif "expensive" in query.lower():
                return "ORDER BY cp.price DESC"
            else:
                return "ORDER BY p.name ASC"
        
        elif step_type == QueryStepType.RESULT_FORMATTING:
            return """
            SELECT 
                p.id as product_id,
                p.name as product_name,
                pl.name as platform_name,
                cp.price as current_price,
                cp.original_price,
                cp.discount_percentage,
                cp.is_available,
                cp.last_updated
            FROM products p
            JOIN current_prices cp ON p.id = cp.product_id
            JOIN platforms pl ON cp.platform_id = pl.id
            """
        
        return "-- SQL fragment placeholder"
    
    def _extract_product_name(self, query: str) -> str:
        """Extract product name from query (simplified version)."""
        query_lower = query.lower()
        
        # Common products
        products = ["onion", "onions", "tomato", "tomatoes", "potato", "potatoes", 
                   "apple", "apples", "banana", "bananas", "milk", "bread", "rice",
                   "oil", "sugar", "salt", "flour", "dal", "pulses"]
        
        for product in products:
            if product in query_lower:
                return product
        
        # Extract from context words
        words = query_lower.split()
        for i, word in enumerate(words):
            if word in ["cheapest", "price", "cost", "find", "show"] and i + 1 < len(words):
                return words[i + 1]
        
        return "product"
    
    async def _customize_validation_query(
        self,
        template_query: str,
        query: str,
        context: Optional[Dict] = None
    ) -> str:
        """Customize validation query template with actual values."""
        customized = template_query
        
        # Replace placeholders
        if "{product_name}" in customized:
            product_name = self._extract_product_name(query)
            customized = customized.replace("{product_name}", product_name)
        
        if "{min_discount}" in customized:
            min_discount = self._extract_discount_percentage(query)
            customized = customized.replace("{min_discount}", str(min_discount))
        
        if "{search_term}" in customized:
            search_term = self._extract_product_name(query)
            customized = customized.replace("{search_term}", search_term)
        
        if "{tables}" in customized:
            # This would be filled with actual table names
            customized = customized.replace("{tables}", "'products', 'current_prices', 'platforms'")
        
        return customized
    
    def _extract_discount_percentage(self, query: str) -> float:
        """Extract discount percentage from query."""
        import re
        
        percentage_match = re.search(r'(\d+)%', query)
        if percentage_match:
            return float(percentage_match.group(1))
        
        percent_match = re.search(r'(\d+)\s*percent', query)
        if percent_match:
            return float(percent_match.group(1))
        
        return 0.0
    
    async def execute_plan(self, execution_plan: QueryExecutionPlan) -> MultiStepQueryResult:
        """
        Execute a multi-step query plan with validation and error recovery.
        
        Args:
            execution_plan: The execution plan to run
            
        Returns:
            MultiStepQueryResult with execution details and final result
        """
        logger.info(f"Executing plan {execution_plan.query_id} with {len(execution_plan.steps)} steps")
        
        start_time = time.time()
        step_results = []
        steps_executed = 0
        steps_failed = 0
        error_recovery_applied = False
        final_result = None
        
        try:
            # Execute steps in dependency order
            for step in execution_plan.steps:
                # Check if dependencies are satisfied
                if not await self._check_step_dependencies(step, step_results):
                    logger.warning(f"Skipping step {step.step_id} - dependencies not satisfied")
                    step.status = StepStatus.SKIPPED
                    continue
                
                # Execute step with validation
                step_result = await self._execute_step_with_validation(step)
                step_results.append(step_result)
                steps_executed += 1
                
                if not step_result.success:
                    steps_failed += 1
                    
                    # Apply error recovery if possible
                    recovery_result = await self._apply_error_recovery(step, step_result)
                    if recovery_result.success:
                        error_recovery_applied = True
                        step_results[-1] = recovery_result  # Replace failed result
                        logger.info(f"Error recovery successful for step {step.step_id}")
                    else:
                        logger.error(f"Step {step.step_id} failed and recovery unsuccessful")
                        # Continue with remaining steps if not critical
                        if step.step_type in [QueryStepType.TABLE_SELECTION, QueryStepType.DATA_VALIDATION]:
                            break  # Critical failure
            
            # Aggregate results from all successful steps
            final_result = await self._aggregate_step_results(step_results, execution_plan)
            
            total_execution_time = time.time() - start_time
            
            # Generate suggestions based on execution
            suggestions = self._generate_execution_suggestions(step_results, execution_plan)
            
            result = MultiStepQueryResult(
                query_id=execution_plan.query_id,
                original_query=execution_plan.original_query,
                success=steps_failed == 0 or final_result is not None,
                final_result=final_result,
                total_execution_time=total_execution_time,
                steps_executed=steps_executed,
                steps_failed=steps_failed,
                step_results=step_results,
                error_recovery_applied=error_recovery_applied,
                suggestions=suggestions
            )
            
            logger.info(f"Plan execution completed: {steps_executed} steps executed, "
                       f"{steps_failed} failed, recovery applied: {error_recovery_applied}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing plan {execution_plan.query_id}: {str(e)}")
            
            return MultiStepQueryResult(
                query_id=execution_plan.query_id,
                original_query=execution_plan.original_query,
                success=False,
                final_result=None,
                total_execution_time=time.time() - start_time,
                steps_executed=steps_executed,
                steps_failed=steps_failed + 1,
                step_results=step_results,
                error_recovery_applied=error_recovery_applied,
                suggestions=["Query execution failed due to system error", "Please try again with a simpler query"]
            )
        
        finally:
            # Clean up active execution
            if execution_plan.query_id in self.active_executions:
                del self.active_executions[execution_plan.query_id]
    
    async def _check_step_dependencies(
        self, 
        step: QueryStep, 
        completed_results: List[StepExecutionResult]
    ) -> bool:
        """Check if all dependencies for a step are satisfied."""
        if not step.dependencies:
            return True
        
        completed_step_ids = {result.step_id for result in completed_results if result.success}
        return all(dep_id in completed_step_ids for dep_id in step.dependencies)
    
    async def _execute_step_with_validation(self, step: QueryStep) -> StepExecutionResult:
        """Execute a single step with validation."""
        logger.debug(f"Executing step {step.step_id}: {step.description}")
        
        step.status = StepStatus.IN_PROGRESS
        start_time = time.time()
        
        try:
            # Run validation query first if provided
            if step.validation_query:
                validation_success = await self._run_validation_query(step.validation_query)
                if not validation_success:
                    step.status = StepStatus.FAILED
                    return StepExecutionResult(
                        step_id=step.step_id,
                        success=False,
                        result=None,
                        execution_time=time.time() - start_time,
                        error_message="Validation query failed",
                        suggestions=self.recovery_strategies.get(step.step_type, [])
                    )
            
            # Execute main step logic
            result = await self._execute_step_logic(step)
            
            step.status = StepStatus.COMPLETED
            step.result = result
            step.execution_time = time.time() - start_time
            
            return StepExecutionResult(
                step_id=step.step_id,
                success=True,
                result=result,
                execution_time=step.execution_time
            )
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error_message = str(e)
            step.execution_time = time.time() - start_time
            
            logger.error(f"Step {step.step_id} failed: {str(e)}")
            
            return StepExecutionResult(
                step_id=step.step_id,
                success=False,
                result=None,
                execution_time=step.execution_time,
                error_message=str(e),
                suggestions=self.recovery_strategies.get(step.step_type, [])
            )
    
    async def _run_validation_query(self, validation_query: str) -> bool:
        """Run a validation query and return success status."""
        try:
            with SessionLocal() as db:
                result = db.execute(text(validation_query))
                
                # For COUNT queries, check if count > 0
                if "COUNT(*)" in validation_query.upper():
                    count = result.scalar()
                    return count > 0
                
                # For existence queries, check if any rows returned
                rows = result.fetchall()
                return len(rows) > 0
                
        except Exception as e:
            logger.warning(f"Validation query failed: {str(e)}")
            return False
    
    async def _execute_step_logic(self, step: QueryStep) -> Any:
        """Execute the main logic for a query step."""
        
        if step.step_type == QueryStepType.TABLE_SELECTION:
            # Return list of selected tables
            return {"selected_tables": step.sql_fragment.replace("-- Using tables: ", "").split(", ")}
        
        elif step.step_type == QueryStepType.DATA_VALIDATION:
            # Execute validation and return count
            with SessionLocal() as db:
                result = db.execute(text(step.sql_fragment))
                count = result.scalar()
                return {"validation_count": count, "valid": count > 0}
        
        elif step.step_type == QueryStepType.JOIN_VALIDATION:
            # Test join and return success
            with SessionLocal() as db:
                result = db.execute(text(step.sql_fragment))
                count = result.scalar()
                return {"join_valid": count > 0}
        
        elif step.step_type == QueryStepType.FILTER_APPLICATION:
            # Return filter information
            return {"filters_applied": step.sql_fragment}
        
        elif step.step_type == QueryStepType.AGGREGATION:
            # Return aggregation info
            return {"aggregation": step.sql_fragment}
        
        elif step.step_type == QueryStepType.RESULT_FORMATTING:
            # Execute final query and return formatted results
            with SessionLocal() as db:
                result = db.execute(text(step.sql_fragment + " LIMIT 50"))  # Limit for safety
                rows = result.fetchall()
                
                # Convert to list of dictionaries
                columns = result.keys()
                formatted_results = []
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    formatted_results.append(row_dict)
                
                return {"formatted_results": formatted_results, "count": len(formatted_results)}
        
        return {"step_completed": True}
    
    async def _apply_error_recovery(
        self, 
        failed_step: QueryStep, 
        failed_result: StepExecutionResult
    ) -> StepExecutionResult:
        """Apply error recovery strategies for a failed step."""
        logger.info(f"Applying error recovery for step {failed_step.step_id}")
        
        recovery_strategies = self.recovery_strategies.get(failed_step.step_type, [])
        
        for strategy in recovery_strategies:
            try:
                # Apply recovery strategy based on step type
                if failed_step.step_type == QueryStepType.DATA_VALIDATION:
                    # Try broader search criteria
                    modified_query = failed_step.sql_fragment.replace("ILIKE '%", "ILIKE '%")
                    modified_query = modified_query.replace("%'", "%'")  # Keep as is for now
                    
                    with SessionLocal() as db:
                        result = db.execute(text(modified_query))
                        count = result.scalar()
                        
                        if count > 0:
                            return StepExecutionResult(
                                step_id=failed_step.step_id,
                                success=True,
                                result={"validation_count": count, "valid": True, "recovery_applied": strategy},
                                execution_time=failed_result.execution_time,
                                suggestions=[]
                            )
                
                elif failed_step.step_type == QueryStepType.JOIN_VALIDATION:
                    # Try LEFT JOIN instead of INNER JOIN
                    modified_query = failed_step.sql_fragment.replace("JOIN", "LEFT JOIN")
                    
                    with SessionLocal() as db:
                        result = db.execute(text(modified_query))
                        count = result.scalar()
                        
                        if count > 0:
                            return StepExecutionResult(
                                step_id=failed_step.step_id,
                                success=True,
                                result={"join_valid": True, "recovery_applied": strategy},
                                execution_time=failed_result.execution_time,
                                suggestions=[]
                            )
                
                # Add more recovery strategies as needed
                
            except Exception as e:
                logger.warning(f"Recovery strategy '{strategy}' failed: {str(e)}")
                continue
        
        # If all recovery strategies fail, return the original failed result
        return failed_result
    
    async def _aggregate_step_results(
        self, 
        step_results: List[StepExecutionResult], 
        execution_plan: QueryExecutionPlan
    ) -> Any:
        """Aggregate results from all successful steps into final result."""
        
        # Find the final result formatting step
        final_result = None
        for result in reversed(step_results):
            if result.success and isinstance(result.result, dict):
                if "formatted_results" in result.result:
                    final_result = result.result["formatted_results"]
                    break
        
        # If no formatted results, try to construct from available data
        if final_result is None:
            # Look for any successful step with useful data
            for result in step_results:
                if result.success and result.result:
                    if isinstance(result.result, dict) and "validation_count" in result.result:
                        final_result = {"message": f"Found {result.result['validation_count']} matching items"}
                        break
        
        # Default fallback
        if final_result is None:
            final_result = {"message": "Query executed but no results available"}
        
        return final_result
    
    def _generate_execution_suggestions(
        self, 
        step_results: List[StepExecutionResult], 
        execution_plan: QueryExecutionPlan
    ) -> List[str]:
        """Generate suggestions based on step execution results."""
        suggestions = []
        
        failed_steps = [r for r in step_results if not r.success]
        
        if failed_steps:
            suggestions.append("Some query steps failed - try simplifying your query")
            
            # Add specific suggestions based on failed step types
            for failed_step in failed_steps:
                if failed_step.suggestions:
                    suggestions.extend(failed_step.suggestions[:2])  # Limit suggestions
        
        if execution_plan.complexity_score >= 8:
            suggestions.append("This was a complex query - consider breaking it into smaller parts")
        
        if len(step_results) > 5:
            suggestions.append("Query required many steps - simpler queries will be faster")
        
        return suggestions[:5]  # Limit to top 5 suggestions


# Singleton instance for global use
_multi_step_processor_instance = None

def get_multi_step_processor() -> MultiStepQueryProcessor:
    """Get singleton instance of MultiStepQueryProcessor."""
    global _multi_step_processor_instance
    if _multi_step_processor_instance is None:
        _multi_step_processor_instance = MultiStepQueryProcessor()
    return _multi_step_processor_instance