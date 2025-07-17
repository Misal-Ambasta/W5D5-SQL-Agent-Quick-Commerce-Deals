"""
Query Planner and Optimizer for Quick Commerce Deals platform.
Provides intelligent query planning, join optimization, and execution plan generation.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
from enum import Enum
import networkx as nx
from sqlalchemy import text, inspect, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import engine
from app.services.semantic_indexer import get_semantic_indexer
from app.core.cache import cache_manager, CacheNamespace

logger = logging.getLogger(__name__)


class JoinType(Enum):
    """Enumeration of SQL join types"""
    INNER = "INNER JOIN"
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    FULL = "FULL OUTER JOIN"


class QueryComplexity(Enum):
    """Query complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


@dataclass
class JoinPath:
    """Represents a join path between two tables"""
    from_table: str
    to_table: str
    join_type: JoinType
    condition: str
    cost_estimate: float
    confidence: float


@dataclass
class QueryExecutionPlan:
    """Represents a complete query execution plan"""
    tables: List[str]
    join_order: List[str]
    join_paths: List[JoinPath]
    estimated_cost: float
    complexity: QueryComplexity
    optimization_suggestions: List[str]
    index_recommendations: List[str]
    execution_time_estimate: float


class QueryPlanner:
    """
    Advanced query planner for optimal join path determination and query optimization.
    Uses graph analysis and cost-based optimization for multi-table queries.
    """
    
    def __init__(self):
        """Initialize the query planner with database schema analysis."""
        self.engine = engine
        self.Session = sessionmaker(bind=self.engine)
        
        # Graph for table relationships
        self.join_graph = nx.Graph()
        
        # Schema metadata
        self.schema_metadata = {}
        self.table_sizes = {}
        self.index_info = {}
        
        # Cost estimation parameters
        self.base_table_scan_cost = 1.0
        self.join_cost_multiplier = 2.0
        self.index_scan_cost_reduction = 0.3
        
        # Initialize schema analysis
        self._analyze_database_schema()
        self._build_join_graph()
        self._estimate_table_sizes()
        
        # Get semantic indexer for intelligent table selection
        try:
            self.semantic_indexer = get_semantic_indexer()
        except Exception as e:
            logger.warning(f"Could not initialize semantic indexer: {str(e)}")
            self.semantic_indexer = None
    
    def _analyze_database_schema(self):
        """Analyze database schema to understand table structures and relationships."""
        logger.info("Analyzing database schema for query planning...")
        
        try:
            inspector = inspect(self.engine)
            table_names = inspector.get_table_names()
            
            for table_name in table_names:
                # Get table metadata
                columns = inspector.get_columns(table_name)
                foreign_keys = inspector.get_foreign_keys(table_name)
                indexes = inspector.get_indexes(table_name)
                primary_keys = inspector.get_pk_constraint(table_name)
                
                self.schema_metadata[table_name] = {
                    'columns': {col['name']: col for col in columns},
                    'foreign_keys': foreign_keys,
                    'indexes': indexes,
                    'primary_keys': primary_keys.get('constrained_columns', [])
                }
                
                # Store index information for cost estimation
                self.index_info[table_name] = {
                    'indexed_columns': set(),
                    'unique_indexes': set(),
                    'composite_indexes': []
                }
                
                for index in indexes:
                    columns_in_index = index['column_names']
                    if len(columns_in_index) == 1:
                        self.index_info[table_name]['indexed_columns'].add(columns_in_index[0])
                        if index.get('unique', False):
                            self.index_info[table_name]['unique_indexes'].add(columns_in_index[0])
                    else:
                        self.index_info[table_name]['composite_indexes'].append(columns_in_index)
            
            logger.info(f"Analyzed schema for {len(table_names)} tables")
            
        except Exception as e:
            logger.error(f"Error analyzing database schema: {str(e)}")
            raise
    
    def _build_join_graph(self):
        """Build a graph representing possible joins between tables."""
        logger.info("Building join graph for query optimization...")
        
        # Add all tables as nodes
        for table_name in self.schema_metadata.keys():
            self.join_graph.add_node(table_name, table_info=self.schema_metadata[table_name])
        
        # Add edges for foreign key relationships
        for table_name, metadata in self.schema_metadata.items():
            for fk in metadata['foreign_keys']:
                referenced_table = fk['referred_table']
                if referenced_table in self.schema_metadata:
                    
                    # Calculate join cost based on table characteristics
                    join_cost = self._estimate_join_cost(table_name, referenced_table, fk)
                    
                    # Add edge with join information
                    self.join_graph.add_edge(
                        table_name,
                        referenced_table,
                        foreign_key=fk,
                        join_cost=join_cost,
                        join_type=JoinType.INNER
                    )
        
        logger.info(f"Built join graph with {self.join_graph.number_of_nodes()} nodes and {self.join_graph.number_of_edges()} edges")
    
    def _estimate_table_sizes(self):
        """Estimate table sizes for cost-based optimization."""
        logger.info("Estimating table sizes for cost calculation...")
        
        try:
            with self.Session() as session:
                for table_name in self.schema_metadata.keys():
                    try:
                        # Get approximate row count
                        result = session.execute(
                            text(f"SELECT COUNT(*) FROM {table_name}")
                        )
                        row_count = result.scalar()
                        self.table_sizes[table_name] = row_count
                        
                    except Exception as e:
                        logger.warning(f"Could not get size for table {table_name}: {str(e)}")
                        # Use default estimate
                        self.table_sizes[table_name] = 1000
            
            logger.info(f"Estimated sizes for {len(self.table_sizes)} tables")
            
        except Exception as e:
            logger.error(f"Error estimating table sizes: {str(e)}")
            # Use default sizes
            for table_name in self.schema_metadata.keys():
                self.table_sizes[table_name] = 1000
    
    def _estimate_join_cost(self, table1: str, table2: str, foreign_key: Dict) -> float:
        """Estimate the cost of joining two tables."""
        # Base cost calculation
        size1 = self.table_sizes.get(table1, 1000)
        size2 = self.table_sizes.get(table2, 1000)
        
        # Cost is roughly proportional to the product of table sizes
        base_cost = (size1 * size2) / 1000000  # Normalize
        
        # Reduce cost if there are indexes on join columns
        fk_columns = foreign_key.get('constrained_columns', [])
        ref_columns = foreign_key.get('referred_columns', [])
        
        cost_reduction = 1.0
        
        # Check for indexes on foreign key columns
        table1_indexes = self.index_info.get(table1, {}).get('indexed_columns', set())
        table2_indexes = self.index_info.get(table2, {}).get('indexed_columns', set())
        
        if any(col in table1_indexes for col in fk_columns):
            cost_reduction *= self.index_scan_cost_reduction
        
        if any(col in table2_indexes for col in ref_columns):
            cost_reduction *= self.index_scan_cost_reduction
        
        return base_cost * cost_reduction
    
    async def create_execution_plan(
        self, 
        query: str, 
        relevant_tables: List[str],
        query_context: Optional[Dict[str, Any]] = None
    ) -> QueryExecutionPlan:
        """
        Create an optimized execution plan for multi-table queries.
        
        Args:
            query: Natural language query
            relevant_tables: List of tables identified as relevant
            query_context: Additional context for optimization
            
        Returns:
            QueryExecutionPlan with optimized join order and suggestions
        """
        logger.info(f"Creating execution plan for {len(relevant_tables)} tables")
        
        try:
            # Create cache key for this execution plan
            import hashlib
            plan_params = f"{query}_{sorted(relevant_tables)}_{query_context}"
            plan_hash = hashlib.md5(plan_params.encode()).hexdigest()
            
            # Try to get cached execution plan
            cached_plan_data = await cache_manager.get_execution_plan(plan_hash)
            if cached_plan_data:
                logger.debug(f"Retrieved execution plan from cache for query: '{query[:50]}...'")
                # Reconstruct QueryExecutionPlan from cached data
                return QueryExecutionPlan(
                    tables=cached_plan_data['tables'],
                    join_order=cached_plan_data['join_order'],
                    join_paths=[
                        JoinPath(
                            from_table=jp['from_table'],
                            to_table=jp['to_table'],
                            join_type=JoinType(jp['join_type']),
                            condition=jp['condition'],
                            cost_estimate=jp['cost_estimate'],
                            confidence=jp['confidence']
                        ) for jp in cached_plan_data['join_paths']
                    ],
                    estimated_cost=cached_plan_data['estimated_cost'],
                    complexity=QueryComplexity(cached_plan_data['complexity']),
                    optimization_suggestions=cached_plan_data['optimization_suggestions'],
                    index_recommendations=cached_plan_data['index_recommendations'],
                    execution_time_estimate=cached_plan_data['execution_time_estimate']
                )
            
            # Validate tables exist in schema
            valid_tables = [t for t in relevant_tables if t in self.schema_metadata]
            if not valid_tables:
                raise ValueError("No valid tables found in relevant_tables")
            
            # Find optimal join paths
            join_paths = self._find_optimal_join_paths(valid_tables)
            
            # Determine optimal join order
            join_order = self._optimize_join_order(valid_tables, join_paths)
            
            # Calculate total cost estimate
            total_cost = sum(path.cost_estimate for path in join_paths)
            
            # Determine query complexity
            complexity = self._assess_query_complexity(valid_tables, join_paths)
            
            # Generate optimization suggestions
            optimization_suggestions = self._generate_optimization_suggestions(
                query, valid_tables, join_paths, complexity
            )
            
            # Generate index recommendations
            index_recommendations = self._generate_index_recommendations(
                valid_tables, join_paths
            )
            
            # Estimate execution time
            execution_time_estimate = self._estimate_execution_time(
                total_cost, complexity, len(valid_tables)
            )
            
            execution_plan = QueryExecutionPlan(
                tables=valid_tables,
                join_order=join_order,
                join_paths=join_paths,
                estimated_cost=total_cost,
                complexity=complexity,
                optimization_suggestions=optimization_suggestions,
                index_recommendations=index_recommendations,
                execution_time_estimate=execution_time_estimate
            )
            
            # Cache the execution plan
            plan_data = {
                'tables': execution_plan.tables,
                'join_order': execution_plan.join_order,
                'join_paths': [
                    {
                        'from_table': jp.from_table,
                        'to_table': jp.to_table,
                        'join_type': jp.join_type.value,
                        'condition': jp.condition,
                        'cost_estimate': jp.cost_estimate,
                        'confidence': jp.confidence
                    } for jp in execution_plan.join_paths
                ],
                'estimated_cost': execution_plan.estimated_cost,
                'complexity': execution_plan.complexity.value,
                'optimization_suggestions': execution_plan.optimization_suggestions,
                'index_recommendations': execution_plan.index_recommendations,
                'execution_time_estimate': execution_plan.execution_time_estimate
            }
            
            await cache_manager.cache_execution_plan(
                plan_hash, 
                plan_data, 
                tables_used=valid_tables
            )
            
            logger.info(f"Created execution plan with {len(join_paths)} joins, "
                       f"complexity: {complexity.value}, estimated cost: {total_cost:.2f}")
            
            return execution_plan
            
        except Exception as e:
            logger.error(f"Error creating execution plan: {str(e)}")
            # Return a basic plan as fallback
            return self._create_fallback_plan(relevant_tables)
    
    def _find_optimal_join_paths(self, tables: List[str]) -> List[JoinPath]:
        """Find optimal join paths between tables using graph algorithms."""
        if len(tables) <= 1:
            return []
        
        join_paths = []
        
        try:
            # Create subgraph with only relevant tables
            subgraph = self.join_graph.subgraph(tables)
            
            # If graph is not connected, find minimum spanning forest
            if not nx.is_connected(subgraph):
                # Find connected components
                components = list(nx.connected_components(subgraph))
                logger.warning(f"Tables form {len(components)} disconnected components")
                
                # For each component, find minimum spanning tree
                for component in components:
                    if len(component) > 1:
                        component_subgraph = subgraph.subgraph(component)
                        mst = nx.minimum_spanning_tree(component_subgraph, weight='join_cost')
                        join_paths.extend(self._convert_edges_to_join_paths(mst.edges(data=True)))
            else:
                # Find minimum spanning tree for connected graph
                mst = nx.minimum_spanning_tree(subgraph, weight='join_cost')
                join_paths = self._convert_edges_to_join_paths(mst.edges(data=True))
            
        except Exception as e:
            logger.warning(f"Error finding optimal join paths: {str(e)}")
            # Fallback to simple sequential joins
            join_paths = self._create_sequential_joins(tables)
        
        return join_paths
    
    def _convert_edges_to_join_paths(self, edges) -> List[JoinPath]:
        """Convert graph edges to JoinPath objects."""
        join_paths = []
        
        for edge in edges:
            table1, table2, edge_data = edge
            fk_info = edge_data.get('foreign_key', {})
            
            # Determine join direction based on foreign key
            if fk_info:
                fk_columns = fk_info.get('constrained_columns', [])
                ref_columns = fk_info.get('referred_columns', [])
                
                if fk_columns and ref_columns:
                    condition = f"{table1}.{fk_columns[0]} = {table2}.{ref_columns[0]}"
                else:
                    condition = f"{table1}.id = {table2}.id"  # Fallback
            else:
                condition = f"{table1}.id = {table2}.id"  # Fallback
            
            join_path = JoinPath(
                from_table=table1,
                to_table=table2,
                join_type=edge_data.get('join_type', JoinType.INNER),
                condition=condition,
                cost_estimate=edge_data.get('join_cost', 1.0),
                confidence=0.9 if fk_info else 0.5
            )
            
            join_paths.append(join_path)
        
        return join_paths
    
    def _create_sequential_joins(self, tables: List[str]) -> List[JoinPath]:
        """Create simple sequential joins as fallback."""
        join_paths = []
        
        for i in range(len(tables) - 1):
            table1, table2 = tables[i], tables[i + 1]
            
            # Try to find a foreign key relationship
            condition = self._find_join_condition(table1, table2)
            
            join_path = JoinPath(
                from_table=table1,
                to_table=table2,
                join_type=JoinType.INNER,
                condition=condition,
                cost_estimate=self._estimate_join_cost(table1, table2, {}),
                confidence=0.5
            )
            
            join_paths.append(join_path)
        
        return join_paths
    
    def _find_join_condition(self, table1: str, table2: str) -> str:
        """Find appropriate join condition between two tables."""
        # Check for foreign key relationships
        table1_meta = self.schema_metadata.get(table1, {})
        table2_meta = self.schema_metadata.get(table2, {})
        
        # Check if table1 has FK to table2
        for fk in table1_meta.get('foreign_keys', []):
            if fk['referred_table'] == table2:
                fk_col = fk['constrained_columns'][0]
                ref_col = fk['referred_columns'][0]
                return f"{table1}.{fk_col} = {table2}.{ref_col}"
        
        # Check if table2 has FK to table1
        for fk in table2_meta.get('foreign_keys', []):
            if fk['referred_table'] == table1:
                fk_col = fk['constrained_columns'][0]
                ref_col = fk['referred_columns'][0]
                return f"{table2}.{fk_col} = {table1}.{ref_col}"
        
        # Fallback to common column names
        table1_columns = set(table1_meta.get('columns', {}).keys())
        table2_columns = set(table2_meta.get('columns', {}).keys())
        
        common_columns = table1_columns.intersection(table2_columns)
        if common_columns:
            common_col = next(iter(common_columns))
            return f"{table1}.{common_col} = {table2}.{common_col}"
        
        # Last resort - assume id columns
        return f"{table1}.id = {table2}.id"
    
    def _optimize_join_order(self, tables: List[str], join_paths: List[JoinPath]) -> List[str]:
        """Optimize the order of table joins for better performance."""
        if len(tables) <= 2:
            return tables
        
        # Start with the smallest table
        table_sizes = [(table, self.table_sizes.get(table, 1000)) for table in tables]
        table_sizes.sort(key=lambda x: x[1])
        
        ordered_tables = [table_sizes[0][0]]  # Start with smallest table
        remaining_tables = set(tables) - {ordered_tables[0]}
        
        # Greedily add tables that have the lowest cost joins
        while remaining_tables:
            best_table = None
            best_cost = float('inf')
            
            for table in remaining_tables:
                # Find minimum cost to join this table with already ordered tables
                min_cost = float('inf')
                for ordered_table in ordered_tables:
                    for join_path in join_paths:
                        if ((join_path.from_table == table and join_path.to_table == ordered_table) or
                            (join_path.from_table == ordered_table and join_path.to_table == table)):
                            min_cost = min(min_cost, join_path.cost_estimate)
                
                if min_cost < best_cost:
                    best_cost = min_cost
                    best_table = table
            
            if best_table:
                ordered_tables.append(best_table)
                remaining_tables.remove(best_table)
            else:
                # If no connection found, add remaining tables in size order
                remaining_sorted = sorted(remaining_tables, 
                                        key=lambda t: self.table_sizes.get(t, 1000))
                ordered_tables.extend(remaining_sorted)
                break
        
        return ordered_tables
    
    def _assess_query_complexity(self, tables: List[str], join_paths: List[JoinPath]) -> QueryComplexity:
        """Assess the complexity of the query based on tables and joins."""
        num_tables = len(tables)
        num_joins = len(join_paths)
        
        # Calculate total estimated rows
        total_estimated_rows = sum(self.table_sizes.get(table, 1000) for table in tables)
        
        # Complexity scoring with more aggressive scaling
        complexity_score = 0
        
        # Table count factor (more aggressive)
        if num_tables <= 1:
            complexity_score += 1
        elif num_tables <= 2:
            complexity_score += 2
        elif num_tables <= 4:
            complexity_score += 3
        elif num_tables <= 6:
            complexity_score += 4
        else:
            complexity_score += 5
        
        # Join complexity factor (more aggressive)
        if num_joins == 0:
            complexity_score += 1
        elif num_joins <= 2:
            complexity_score += 2
        elif num_joins <= 4:
            complexity_score += 3
        elif num_joins <= 6:
            complexity_score += 4
        else:
            complexity_score += 5
        
        # Data volume factor
        if total_estimated_rows <= 10000:
            complexity_score += 1
        elif total_estimated_rows <= 100000:
            complexity_score += 2
        elif total_estimated_rows <= 1000000:
            complexity_score += 3
        else:
            complexity_score += 4
        
        # Map score to complexity level (adjusted thresholds)
        if complexity_score <= 4:
            return QueryComplexity.SIMPLE
        elif complexity_score <= 7:
            return QueryComplexity.MODERATE
        elif complexity_score <= 11:
            return QueryComplexity.COMPLEX
        else:
            return QueryComplexity.VERY_COMPLEX
    
    def _generate_optimization_suggestions(
        self, 
        query: str, 
        tables: List[str], 
        join_paths: List[JoinPath],
        complexity: QueryComplexity
    ) -> List[str]:
        """Generate optimization suggestions based on query analysis."""
        suggestions = []
        
        # Complexity-based suggestions
        if complexity == QueryComplexity.VERY_COMPLEX:
            suggestions.append("Consider breaking this query into smaller sub-queries")
            suggestions.append("Use LIMIT clause to restrict result set size")
        
        if complexity in [QueryComplexity.COMPLEX, QueryComplexity.VERY_COMPLEX]:
            suggestions.append("Consider adding appropriate WHERE clauses to filter data early")
            suggestions.append("Review if all joined tables are necessary for the result")
        
        # Join-specific suggestions
        high_cost_joins = [jp for jp in join_paths if jp.cost_estimate > 10.0]
        if high_cost_joins:
            suggestions.append(f"High-cost joins detected on {len(high_cost_joins)} table pairs - consider adding indexes")
        
        low_confidence_joins = [jp for jp in join_paths if jp.confidence < 0.7]
        if low_confidence_joins:
            suggestions.append("Some joins may not be optimal - verify join conditions are correct")
        
        # Table-specific suggestions
        large_tables = [t for t in tables if self.table_sizes.get(t, 0) > 100000]
        if large_tables:
            suggestions.append(f"Large tables detected: {', '.join(large_tables)} - ensure proper indexing")
        
        # Query pattern suggestions
        query_lower = query.lower()
        if "price" in query_lower and "current_prices" in tables:
            suggestions.append("For price queries, consider filtering by date range to improve performance")
        
        if "discount" in query_lower:
            suggestions.append("Filter for active discounts only (is_active = true) to reduce result set")
        
        if len(tables) > 5:
            suggestions.append("Consider using materialized views for frequently accessed multi-table queries")
        
        return suggestions[:8]  # Limit to top 8 suggestions
    
    def _generate_index_recommendations(self, tables: List[str], join_paths: List[JoinPath]) -> List[str]:
        """Generate index recommendations based on join patterns."""
        recommendations = []
        
        # Analyze join columns for index recommendations
        join_columns = {}
        for join_path in join_paths:
            # Parse join condition to extract columns
            condition = join_path.condition
            if "=" in condition:
                parts = condition.split("=")
                if len(parts) == 2:
                    left_col = parts[0].strip()
                    right_col = parts[1].strip()
                    
                    # Extract table.column format
                    if "." in left_col:
                        table, col = left_col.split(".", 1)
                        join_columns.setdefault(table, set()).add(col)
                    
                    if "." in right_col:
                        table, col = right_col.split(".", 1)
                        join_columns.setdefault(table, set()).add(col)
        
        # Check which columns need indexes
        for table, columns in join_columns.items():
            if table in self.index_info:
                indexed_cols = self.index_info[table]['indexed_columns']
                missing_indexes = columns - indexed_cols
                
                for col in missing_indexes:
                    recommendations.append(f"CREATE INDEX idx_{table}_{col} ON {table}({col})")
        
        # Recommend composite indexes for multi-column joins
        for table in tables:
            table_join_cols = join_columns.get(table, set())
            if len(table_join_cols) > 1:
                cols_list = sorted(list(table_join_cols))
                recommendations.append(
                    f"CREATE INDEX idx_{table}_composite ON {table}({', '.join(cols_list)})"
                )
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _estimate_execution_time(self, cost: float, complexity: QueryComplexity, num_tables: int) -> float:
        """Estimate query execution time in seconds."""
        base_time = 0.1  # Base execution time in seconds
        
        # Cost factor
        time_estimate = base_time + (cost * 0.01)
        
        # Complexity multiplier
        complexity_multipliers = {
            QueryComplexity.SIMPLE: 1.0,
            QueryComplexity.MODERATE: 1.5,
            QueryComplexity.COMPLEX: 2.5,
            QueryComplexity.VERY_COMPLEX: 4.0
        }
        
        time_estimate *= complexity_multipliers.get(complexity, 1.0)
        
        # Table count factor
        time_estimate *= (1 + (num_tables - 1) * 0.2)
        
        return round(time_estimate, 2)
    
    def _create_fallback_plan(self, tables: List[str]) -> QueryExecutionPlan:
        """Create a basic fallback execution plan."""
        return QueryExecutionPlan(
            tables=tables,
            join_order=tables,
            join_paths=[],
            estimated_cost=len(tables) * 2.0,
            complexity=QueryComplexity.MODERATE,
            optimization_suggestions=["Unable to create optimal plan - using fallback"],
            index_recommendations=[],
            execution_time_estimate=1.0
        )
    
    def optimize_sql_query(self, sql_query: str, execution_plan: QueryExecutionPlan) -> str:
        """
        Apply optimizations to a SQL query based on the execution plan.
        
        Args:
            sql_query: Original SQL query
            execution_plan: Query execution plan with optimization info
            
        Returns:
            Optimized SQL query
        """
        optimized_query = sql_query
        
        try:
            # Add query hints based on execution plan
            if execution_plan.complexity in [QueryComplexity.COMPLEX, QueryComplexity.VERY_COMPLEX]:
                # Add LIMIT if not present and query is complex
                if "LIMIT" not in optimized_query.upper():
                    optimized_query += " LIMIT 1000"
            
            # Add index hints in comments for reference
            if execution_plan.index_recommendations:
                hint_comment = "/* Recommended indexes:\n"
                for rec in execution_plan.index_recommendations[:3]:
                    hint_comment += f"   {rec}\n"
                hint_comment += "*/"
                optimized_query = hint_comment + "\n" + optimized_query
            
            # Add execution plan comment
            plan_comment = f"/* Execution Plan: {len(execution_plan.tables)} tables, " \
                          f"{len(execution_plan.join_paths)} joins, " \
                          f"complexity: {execution_plan.complexity.value} */"
            optimized_query = plan_comment + "\n" + optimized_query
            
            logger.info("Applied query optimizations based on execution plan")
            
        except Exception as e:
            logger.warning(f"Error optimizing SQL query: {str(e)}")
        
        return optimized_query
    
    def analyze_query_performance(self, sql_query: str, execution_time: float) -> Dict[str, Any]:
        """
        Analyze actual query performance and provide insights.
        
        Args:
            sql_query: Executed SQL query
            execution_time: Actual execution time in seconds
            
        Returns:
            Performance analysis with insights and recommendations
        """
        analysis = {
            "execution_time": execution_time,
            "performance_rating": "unknown",
            "bottlenecks": [],
            "recommendations": []
        }
        
        try:
            # Performance rating based on execution time
            if execution_time < 0.1:
                analysis["performance_rating"] = "excellent"
            elif execution_time < 0.5:
                analysis["performance_rating"] = "good"
            elif execution_time < 2.0:
                analysis["performance_rating"] = "acceptable"
            elif execution_time < 5.0:
                analysis["performance_rating"] = "slow"
            else:
                analysis["performance_rating"] = "very_slow"
            
            # Identify potential bottlenecks
            if execution_time > 1.0:
                analysis["bottlenecks"].append("Query execution time exceeds 1 second")
                
                if "JOIN" in sql_query.upper():
                    analysis["bottlenecks"].append("Multiple table joins may be causing slowdown")
                
                if "ORDER BY" in sql_query.upper() and "LIMIT" not in sql_query.upper():
                    analysis["bottlenecks"].append("Sorting without LIMIT may be inefficient")
            
            # Generate recommendations
            if analysis["performance_rating"] in ["slow", "very_slow"]:
                analysis["recommendations"].extend([
                    "Consider adding appropriate indexes on join and filter columns",
                    "Use LIMIT clause to restrict result set size",
                    "Review WHERE clauses to filter data as early as possible"
                ])
            
            if "COUNT(*)" in sql_query.upper():
                analysis["recommendations"].append("Consider using approximate count for large tables")
            
        except Exception as e:
            logger.error(f"Error analyzing query performance: {str(e)}")
        
        return analysis
    
    def get_join_graph_stats(self) -> Dict[str, Any]:
        """Get statistics about the join graph."""
        return {
            "total_tables": self.join_graph.number_of_nodes(),
            "total_relationships": self.join_graph.number_of_edges(),
            "connected_components": nx.number_connected_components(self.join_graph),
            "average_degree": sum(dict(self.join_graph.degree()).values()) / self.join_graph.number_of_nodes() if self.join_graph.number_of_nodes() > 0 else 0,
            "largest_component_size": len(max(nx.connected_components(self.join_graph), key=len)) if self.join_graph.number_of_nodes() > 0 else 0
        }


# Singleton instance for global use
_query_planner_instance = None

def get_query_planner() -> QueryPlanner:
    """Get singleton instance of QueryPlanner."""
    global _query_planner_instance
    if _query_planner_instance is None:
        _query_planner_instance = QueryPlanner()
    return _query_planner_instance