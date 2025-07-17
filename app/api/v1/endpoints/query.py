"""
Natural language query endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
import time
import logging
from datetime import datetime

from app.core.dependencies import get_db
from app.core.validation import InputValidator
from app.core.exceptions import (
    QueryProcessingError, 
    DatabaseError, 
    ProductNotFoundError,
    ValidationError
)
from app.schemas.query import NaturalLanguageQuery, QueryResponse, QueryResult, QueryError
from app.models.product import Product
from app.models.pricing import CurrentPrice
from app.models.platform import Platform
from app.services.multi_step_query import get_multi_step_processor
from app.services.result_processor import get_result_processor, ResultFormat, SamplingMethod, SamplingConfig, PaginationConfig
from app.services.sample_query_handlers import get_sample_query_handlers
from slowapi import Limiter
from slowapi.util import get_remote_address

# Set up logging
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


@router.post("/", response_model=QueryResponse)
@limiter.limit("10/minute")
async def process_natural_language_query(
    request: Request,
    query_request: NaturalLanguageQuery,
    db: Session = Depends(get_db)
):
    """
    Process natural language query and return results using multi-step query processing.
    
    This endpoint converts natural language queries into SQL using multi-step validation
    and returns relevant product pricing and availability information with advanced
    result processing including sampling, pagination, and caching.
    
    Sample queries:
    - "Which app has cheapest onions right now?"
    - "Show products with 30%+ discount on Blinkit"
    - "Compare fruit prices between Zepto and Instamart"
    """
    start_time = time.time()
    
    try:
        # Validate and sanitize the query
        validated_query = InputValidator.validate_query_string(query_request.query)
        
        # Validate user_id if provided
        validated_user_id = None
        if query_request.user_id:
            validated_user_id = InputValidator.sanitize_user_id(query_request.user_id)
        
        # Validate context if provided
        validated_context = None
        if query_request.context:
            validated_context = InputValidator.validate_context_data(query_request.context)
        
        logger.info(f"Processing validated query with multi-step approach: {validated_query}")
        
        # Create user context
        user_context = {}
        if validated_user_id:
            user_context["user_id"] = validated_user_id
        if validated_context:
            user_context.update(validated_context)
        
        # Try multi-step query processing first
        try:
            multi_step_processor = get_multi_step_processor()
            result_processor = get_result_processor()
            
            # Create execution plan
            execution_plan = await multi_step_processor.create_execution_plan(
                validated_query, user_context
            )
            
            # Execute the plan
            multi_step_result = await multi_step_processor.execute_plan(execution_plan)
            
            if multi_step_result.success and multi_step_result.final_result:
                # Convert multi-step results to raw format for result processor
                raw_results = []
                
                if isinstance(multi_step_result.final_result, dict):
                    if "formatted_results" in multi_step_result.final_result:
                        raw_results = multi_step_result.final_result["formatted_results"]
                    elif isinstance(multi_step_result.final_result, list):
                        raw_results = multi_step_result.final_result
                    else:
                        # Single result
                        raw_results = [multi_step_result.final_result]
                elif isinstance(multi_step_result.final_result, list):
                    raw_results = multi_step_result.final_result
                
                # Configure result processing
                pagination_config = PaginationConfig(page=1, page_size=50)
                sampling_config = SamplingConfig(
                    method=SamplingMethod.RANDOM if len(raw_results) > 1000 else SamplingMethod.NONE,
                    sample_size=1000
                )
                
                # Process results with advanced formatting and caching
                processed_result = await result_processor.process_results(
                    raw_results=raw_results,
                    query=validated_query,
                    pagination_config=pagination_config,
                    sampling_config=sampling_config,
                    result_format=ResultFormat.STRUCTURED,
                    query_context=user_context
                )
                
                # Convert processed results to QueryResult format
                results = []
                for item in processed_result.data:
                    result = QueryResult(
                        product_id=item.get("id", 0),
                        product_name=item.get("product_name", ""),
                        platform_name=item.get("platform_name", ""),
                        current_price=item.get("current_price", 0.0),
                        original_price=item.get("original_price"),
                        discount_percentage=item.get("discount_percentage"),
                        is_available=item.get("is_available", True),
                        last_updated=datetime.fromisoformat(item["last_updated"]) if item.get("last_updated") else datetime.utcnow()
                    )
                    results.append(result)
                
                # Use suggestions from multi-step result if available
                suggestions = multi_step_result.suggestions if not results else None
                relevant_tables = execution_plan.relevant_tables
                
                response = QueryResponse(
                    query=validated_query,
                    results=results,
                    execution_time=time.time() - start_time,
                    relevant_tables=relevant_tables,
                    total_results=processed_result.total_count,
                    cached=processed_result.cached,
                    suggestions=suggestions
                )
                
                logger.info(f"Multi-step query processed successfully in {response.execution_time:.2f}s, "
                           f"returned {len(results)} results (total: {processed_result.total_count})")
                return response
            
            else:
                logger.warning("Multi-step processing failed, falling back to basic processing")
                # Fall back to basic processing
                results = await _process_basic_query(db, validated_query)
                suggestions = multi_step_result.suggestions if multi_step_result.suggestions else _generate_query_suggestions(validated_query)
                relevant_tables = ["products", "current_prices", "platforms"]
        
        except Exception as e:
            logger.error(f"Multi-step processing error, falling back to basic processing: {str(e)}")
            # Fall back to basic processing
            results = await _process_basic_query(db, validated_query)
            suggestions = _generate_query_suggestions(validated_query)
            relevant_tables = ["products", "current_prices", "platforms"]
        
        # Check if no results found
        if not results:
            if not suggestions:
                suggestions = _generate_query_suggestions(validated_query)
            logger.info(f"No results found for query: {validated_query}")
        
        execution_time = time.time() - start_time
        
        response = QueryResponse(
            query=validated_query,
            results=results,
            execution_time=execution_time,
            relevant_tables=relevant_tables,
            total_results=len(results),
            cached=False,
            suggestions=suggestions if not results else None
        )
        
        logger.info(f"Query processed successfully in {execution_time:.2f}s, returned {len(results)} results")
        return response
        
    except ValidationError as e:
        logger.warning(f"Query validation failed: {str(e)}")
        raise e
    except SQLAlchemyError as e:
        logger.error(f"Database error during query processing: {str(e)}")
        raise DatabaseError(f"Database operation failed: {str(e)}", operation="query_processing")
    except Exception as e:
        logger.error(f"Unexpected error during query processing: {str(e)}")
        raise QueryProcessingError(f"Failed to process query: {str(e)}", query=query_request.query)


@router.post("/advanced", response_model=QueryResponse)
@limiter.limit("5/minute")
async def process_advanced_query(
    request: Request,
    query_request: NaturalLanguageQuery,
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(20, ge=1, le=100, description="Number of results per page"),
    sampling_method: str = Query("none", description="Sampling method: random, systematic, stratified, top_n, none"),
    sample_size: int = Query(1000, ge=10, le=10000, description="Maximum sample size for large result sets"),
    result_format: str = Query("structured", description="Result format: raw, structured, summary, comparison, chart_data"),
    db: Session = Depends(get_db)
):
    """
    Advanced natural language query processing with configurable pagination, sampling, and formatting.
    
    This endpoint provides fine-grained control over result processing including:
    - Statistical sampling for large datasets
    - Configurable pagination
    - Multiple result formats
    - Advanced caching with TTL
    - Multi-step query validation
    
    Parameters:
    - page: Page number (1-based)
    - page_size: Results per page (1-100)
    - sampling_method: Statistical sampling method
    - sample_size: Maximum samples for large datasets
    - result_format: Output format for results
    
    Sample queries:
    - "Which app has cheapest onions right now?"
    - "Show products with 30%+ discount on Blinkit"
    - "Compare fruit prices between Zepto and Instamart"
    """
    start_time = time.time()
    
    try:
        # Validate and sanitize the query
        validated_query = InputValidator.validate_query_string(query_request.query)
        
        # Validate user_id if provided
        validated_user_id = None
        if query_request.user_id:
            validated_user_id = InputValidator.sanitize_user_id(query_request.user_id)
        
        # Validate context if provided
        validated_context = None
        if query_request.context:
            validated_context = InputValidator.validate_context_data(query_request.context)
        
        logger.info(f"Processing advanced query: {validated_query} (page={page}, page_size={page_size}, sampling={sampling_method})")
        
        # Create user context
        user_context = {}
        if validated_user_id:
            user_context["user_id"] = validated_user_id
        if validated_context:
            user_context.update(validated_context)
        
        # Validate and convert parameters
        try:
            sampling_method_enum = SamplingMethod(sampling_method.lower())
        except ValueError:
            sampling_method_enum = SamplingMethod.NONE
        
        try:
            result_format_enum = ResultFormat(result_format.lower())
        except ValueError:
            result_format_enum = ResultFormat.STRUCTURED
        
        # Configure processing parameters
        pagination_config = PaginationConfig(
            page=page,
            page_size=page_size,
            max_page_size=100
        )
        
        sampling_config = SamplingConfig(
            method=sampling_method_enum,
            sample_size=sample_size,
            confidence_level=0.95,
            margin_of_error=0.05
        )
        
        # Process with multi-step query processor
        try:
            multi_step_processor = get_multi_step_processor()
            result_processor = get_result_processor()
            
            # Create execution plan
            execution_plan = await multi_step_processor.create_execution_plan(
                validated_query, user_context
            )
            
            # Execute the plan
            multi_step_result = await multi_step_processor.execute_plan(execution_plan)
            
            if multi_step_result.success and multi_step_result.final_result:
                # Convert multi-step results to raw format
                raw_results = []
                
                if isinstance(multi_step_result.final_result, dict):
                    if "formatted_results" in multi_step_result.final_result:
                        raw_results = multi_step_result.final_result["formatted_results"]
                    elif isinstance(multi_step_result.final_result, list):
                        raw_results = multi_step_result.final_result
                    else:
                        raw_results = [multi_step_result.final_result]
                elif isinstance(multi_step_result.final_result, list):
                    raw_results = multi_step_result.final_result
                
                # Process results with advanced configuration
                processed_result = await result_processor.process_results(
                    raw_results=raw_results,
                    query=validated_query,
                    pagination_config=pagination_config,
                    sampling_config=sampling_config,
                    result_format=result_format_enum,
                    query_context=user_context
                )
                
                # Convert processed results based on format
                if result_format_enum in [ResultFormat.SUMMARY, ResultFormat.COMPARISON, ResultFormat.CHART_DATA]:
                    # For special formats, return the processed data directly
                    response = QueryResponse(
                        query=validated_query,
                        results=[],  # Empty for special formats
                        execution_time=time.time() - start_time,
                        relevant_tables=execution_plan.relevant_tables,
                        total_results=processed_result.total_count,
                        cached=processed_result.cached,
                        suggestions=multi_step_result.suggestions if not processed_result.data else None
                    )
                    
                    # Add processed data to response metadata
                    response.metadata = {
                        "processed_data": processed_result.data,
                        "format_type": result_format_enum.value,
                        "sampling_applied": processed_result.sampled,
                        "pagination": processed_result.pagination
                    }
                    
                else:
                    # Convert to QueryResult format for structured/raw formats
                    results = []
                    for item in processed_result.data:
                        if isinstance(item, dict):
                            result = QueryResult(
                                product_id=item.get("id", 0),
                                product_name=item.get("product_name", ""),
                                platform_name=item.get("platform_name", ""),
                                current_price=item.get("current_price", 0.0),
                                original_price=item.get("original_price"),
                                discount_percentage=item.get("discount_percentage"),
                                is_available=item.get("is_available", True),
                                last_updated=datetime.fromisoformat(item["last_updated"]) if item.get("last_updated") else datetime.utcnow()
                            )
                            results.append(result)
                    
                    response = QueryResponse(
                        query=validated_query,
                        results=results,
                        execution_time=time.time() - start_time,
                        relevant_tables=execution_plan.relevant_tables,
                        total_results=processed_result.total_count,
                        cached=processed_result.cached,
                        suggestions=multi_step_result.suggestions if not results else None
                    )
                
                logger.info(f"Advanced query processed successfully in {response.execution_time:.2f}s, "
                           f"format: {result_format_enum.value}, sampling: {sampling_method_enum.value}")
                return response
            
            else:
                logger.warning("Multi-step processing failed, falling back to basic processing")
                # Fall back to basic processing with advanced result processing
                basic_results = await _process_basic_query(db, validated_query)
                
                # Convert QueryResult to dict format for result processor
                raw_results = []
                for result in basic_results:
                    raw_results.append({
                        "id": result.product_id,
                        "product_name": result.product_name,
                        "platform_name": result.platform_name,
                        "current_price": result.current_price,
                        "original_price": result.original_price,
                        "discount_percentage": result.discount_percentage,
                        "is_available": result.is_available,
                        "last_updated": result.last_updated.isoformat() if result.last_updated else None
                    })
                
                # Process with advanced configuration
                processed_result = await result_processor.process_results(
                    raw_results=raw_results,
                    query=validated_query,
                    pagination_config=pagination_config,
                    sampling_config=sampling_config,
                    result_format=result_format_enum,
                    query_context=user_context
                )
                
                # Handle different result formats
                if result_format_enum in [ResultFormat.SUMMARY, ResultFormat.COMPARISON, ResultFormat.CHART_DATA]:
                    response = QueryResponse(
                        query=validated_query,
                        results=[],
                        execution_time=time.time() - start_time,
                        relevant_tables=["products", "current_prices", "platforms"],
                        total_results=processed_result.total_count,
                        cached=processed_result.cached,
                        suggestions=multi_step_result.suggestions if multi_step_result.suggestions else None
                    )
                    response.metadata = {
                        "processed_data": processed_result.data,
                        "format_type": result_format_enum.value,
                        "sampling_applied": processed_result.sampled,
                        "pagination": processed_result.pagination
                    }
                else:
                    # Convert back to QueryResult format
                    results = []
                    for item in processed_result.data:
                        if isinstance(item, dict):
                            result = QueryResult(
                                product_id=item.get("id", 0),
                                product_name=item.get("product_name", ""),
                                platform_name=item.get("platform_name", ""),
                                current_price=item.get("current_price", 0.0),
                                original_price=item.get("original_price"),
                                discount_percentage=item.get("discount_percentage"),
                                is_available=item.get("is_available", True),
                                last_updated=datetime.fromisoformat(item["last_updated"]) if item.get("last_updated") else datetime.utcnow()
                            )
                            results.append(result)
                    
                    response = QueryResponse(
                        query=validated_query,
                        results=results,
                        execution_time=time.time() - start_time,
                        relevant_tables=["products", "current_prices", "platforms"],
                        total_results=processed_result.total_count,
                        cached=processed_result.cached,
                        suggestions=_generate_query_suggestions(validated_query) if not results else None
                    )
                
                return response
        
        except Exception as e:
            logger.error(f"Advanced processing error, falling back to basic processing: {str(e)}")
            # Final fallback to basic processing without advanced features
            results = await _process_basic_query(db, validated_query)
            
            response = QueryResponse(
                query=validated_query,
                results=results,
                execution_time=time.time() - start_time,
                relevant_tables=["products", "current_prices", "platforms"],
                total_results=len(results),
                cached=False,
                suggestions=_generate_query_suggestions(validated_query) if not results else None
            )
            
            return response
        
    except ValidationError as e:
        logger.warning(f"Advanced query validation failed: {str(e)}")
        raise e
    except SQLAlchemyError as e:
        logger.error(f"Database error during advanced query processing: {str(e)}")
        raise DatabaseError(f"Database operation failed: {str(e)}", operation="advanced_query_processing")
    except Exception as e:
        logger.error(f"Unexpected error during advanced query processing: {str(e)}")
        raise QueryProcessingError(f"Failed to process advanced query: {str(e)}", query=query_request.query)


async def _process_basic_query(db: Session, query: str) -> List[QueryResult]:
    """
    Enhanced query processing logic using sample query handlers.
    Implements specific sample queries as required in task 8.1.
    """
    results = []
    query_lower = query.lower()
    
    try:
        # Get sample query handlers
        sample_handlers = get_sample_query_handlers()
        
        # Handle "cheapest" queries (Requirement 10.1)
        if "cheapest" in query_lower:
            results = await sample_handlers.handle_cheapest_product_query(db, query)
        
        # Handle discount queries (Requirement 10.2)
        elif "discount" in query_lower or "%" in query_lower:
            results = await sample_handlers.handle_discount_query(db, query)
        
        # Handle comparison queries (Requirement 10.3)
        elif "compare" in query_lower:
            results = await sample_handlers.handle_price_comparison_query(db, query)
        
        # Handle budget optimization queries (Requirement 10.4)
        elif any(word in query_lower for word in ["₹", "rs", "rupees", "budget", "grocery list", "deals for"]):
            results = await sample_handlers.handle_budget_optimization_query(db, query)
        
        # Fallback: use existing basic logic for other queries
        else:
            # Handle basic product search
            product_name = _extract_product_name(query_lower)
            if product_name:
                results = await _search_products(db, product_name)
            else:
                # Try cheapest query as fallback if no specific pattern matched
                results = await sample_handlers.handle_cheapest_product_query(db, query)
    
    except Exception as e:
        logger.error(f"Error in enhanced query processing: {str(e)}")
        raise
    
    return results


def _extract_product_name(query: str) -> str:
    """Extract product name from query"""
    # Simple keyword extraction - will be improved with NLP
    common_products = ["onion", "onions", "tomato", "tomatoes", "potato", "potatoes", 
                      "apple", "apples", "banana", "bananas", "milk", "bread", "rice"]
    
    for product in common_products:
        if product in query:
            return product
    
    # If no common product found, try to extract from context
    words = query.split()
    for i, word in enumerate(words):
        if word in ["cheapest", "price", "cost"] and i + 1 < len(words):
            return words[i + 1]
    
    return ""


def _extract_platform_name(query: str) -> str:
    """Extract platform name from query"""
    platforms = ["blinkit", "zepto", "instamart", "bigbasket", "swiggy"]
    
    for platform in platforms:
        if platform in query:
            return platform.title()
    
    return ""


def _extract_discount_percentage(query: str) -> float:
    """Extract discount percentage from query"""
    import re
    
    # Look for patterns like "30%", "30 percent", etc.
    percentage_match = re.search(r'(\d+)%', query)
    if percentage_match:
        return float(percentage_match.group(1))
    
    percent_match = re.search(r'(\d+)\s*percent', query)
    if percent_match:
        return float(percent_match.group(1))
    
    return 0.0


def _extract_platforms_for_comparison(query: str) -> List[str]:
    """Extract platform names for comparison"""
    platforms = []
    platform_names = ["blinkit", "zepto", "instamart", "bigbasket", "swiggy"]
    
    for platform in platform_names:
        if platform in query:
            platforms.append(platform.title())
    
    return platforms


async def _find_cheapest_product(db: Session, product_name: str) -> List[QueryResult]:
    """Find cheapest price for a product across all platforms"""
    try:
        query = db.query(
            Product.id,
            Product.name,
            Platform.name.label('platform_name'),
            CurrentPrice.price,
            CurrentPrice.original_price,
            CurrentPrice.discount_percentage,
            CurrentPrice.is_available,
            CurrentPrice.last_updated
        ).join(
            CurrentPrice, Product.id == CurrentPrice.product_id
        ).join(
            Platform, CurrentPrice.platform_id == Platform.id
        ).filter(
            Product.name.ilike(f'%{product_name}%'),
            CurrentPrice.is_available == True,
            Platform.is_active == True
        ).order_by(CurrentPrice.price.asc()).limit(10)
        
        rows = query.all()
        
        return [
            QueryResult(
                product_id=row.id,
                product_name=row.name,
                platform_name=row.platform_name,
                current_price=float(row.price),
                original_price=float(row.original_price) if row.original_price else None,
                discount_percentage=float(row.discount_percentage) if row.discount_percentage else None,
                is_available=row.is_available,
                last_updated=row.last_updated
            )
            for row in rows
        ]
    
    except Exception as e:
        logger.error(f"Error finding cheapest product: {str(e)}")
        return []


async def _find_discounted_products(db: Session, platform_name: str, min_discount: float) -> List[QueryResult]:
    """Find products with discounts above minimum threshold"""
    try:
        query = db.query(
            Product.id,
            Product.name,
            Platform.name.label('platform_name'),
            CurrentPrice.price,
            CurrentPrice.original_price,
            CurrentPrice.discount_percentage,
            CurrentPrice.is_available,
            CurrentPrice.last_updated
        ).join(
            CurrentPrice, Product.id == CurrentPrice.product_id
        ).join(
            Platform, CurrentPrice.platform_id == Platform.id
        ).filter(
            CurrentPrice.discount_percentage >= min_discount,
            CurrentPrice.is_available == True,
            Platform.is_active == True
        )
        
        if platform_name:
            query = query.filter(Platform.name.ilike(f'%{platform_name}%'))
        
        rows = query.order_by(CurrentPrice.discount_percentage.desc()).limit(20).all()
        
        return [
            QueryResult(
                product_id=row.id,
                product_name=row.name,
                platform_name=row.platform_name,
                current_price=float(row.price),
                original_price=float(row.original_price) if row.original_price else None,
                discount_percentage=float(row.discount_percentage) if row.discount_percentage else None,
                is_available=row.is_available,
                last_updated=row.last_updated
            )
            for row in rows
        ]
    
    except Exception as e:
        logger.error(f"Error finding discounted products: {str(e)}")
        return []


async def _compare_product_prices(db: Session, product_name: str, platforms: List[str]) -> List[QueryResult]:
    """Compare product prices across specified platforms"""
    try:
        query = db.query(
            Product.id,
            Product.name,
            Platform.name.label('platform_name'),
            CurrentPrice.price,
            CurrentPrice.original_price,
            CurrentPrice.discount_percentage,
            CurrentPrice.is_available,
            CurrentPrice.last_updated
        ).join(
            CurrentPrice, Product.id == CurrentPrice.product_id
        ).join(
            Platform, CurrentPrice.platform_id == Platform.id
        ).filter(
            Product.name.ilike(f'%{product_name}%'),
            Platform.is_active == True
        )
        
        if platforms:
            query = query.filter(Platform.name.in_(platforms))
        
        rows = query.order_by(CurrentPrice.price.asc()).all()
        
        return [
            QueryResult(
                product_id=row.id,
                product_name=row.name,
                platform_name=row.platform_name,
                current_price=float(row.price),
                original_price=float(row.original_price) if row.original_price else None,
                discount_percentage=float(row.discount_percentage) if row.discount_percentage else None,
                is_available=row.is_available,
                last_updated=row.last_updated
            )
            for row in rows
        ]
    
    except Exception as e:
        logger.error(f"Error comparing product prices: {str(e)}")
        return []


async def _search_products(db: Session, product_name: str) -> List[QueryResult]:
    """General product search"""
    try:
        query = db.query(
            Product.id,
            Product.name,
            Platform.name.label('platform_name'),
            CurrentPrice.price,
            CurrentPrice.original_price,
            CurrentPrice.discount_percentage,
            CurrentPrice.is_available,
            CurrentPrice.last_updated
        ).join(
            CurrentPrice, Product.id == CurrentPrice.product_id
        ).join(
            Platform, CurrentPrice.platform_id == Platform.id
        ).filter(
            Product.name.ilike(f'%{product_name}%'),
            Platform.is_active == True
        ).order_by(CurrentPrice.price.asc()).limit(15)
        
        rows = query.all()
        
        return [
            QueryResult(
                product_id=row.id,
                product_name=row.name,
                platform_name=row.platform_name,
                current_price=float(row.price),
                original_price=float(row.original_price) if row.original_price else None,
                discount_percentage=float(row.discount_percentage) if row.discount_percentage else None,
                is_available=row.is_available,
                last_updated=row.last_updated
            )
            for row in rows
        ]
    
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        return []


def _generate_query_suggestions(query: str) -> List[str]:
    """Generate helpful suggestions when no results are found"""
    suggestions = [
        "Try using more general product names (e.g., 'onion' instead of 'red onion')",
        "Check spelling and try alternative product names",
        "Use platform names like Blinkit, Zepto, Instamart, or BigBasket",
        "Try queries like 'cheapest [product]' or 'compare [product] prices'"
    ]
    
    # Add specific suggestions based on query content
    query_lower = query.lower()
    
    if "cheapest" in query_lower:
        suggestions.insert(0, "Make sure the product name is spelled correctly")
    elif "discount" in query_lower or "%" in query_lower:
        suggestions.insert(0, "Try lowering the discount percentage threshold")
    elif "compare" in query_lower:
        suggestions.insert(0, "Ensure you've specified valid platform names")
    
    return suggestions