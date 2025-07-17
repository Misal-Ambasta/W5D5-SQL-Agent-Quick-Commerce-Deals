"""
Product comparison endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
import time
import logging

from app.core.dependencies import get_db
from app.core.validation import InputValidator
from app.core.exceptions import (
    ValidationError,
    DatabaseError,
    ProductNotFoundError,
    PlatformNotFoundError
)
from app.schemas.products import (
    ProductComparisonRequest, ProductComparisonResponse, ProductComparison,
    ProductInfo, ProductPrice
)
from app.models.product import Product, ProductBrand, ProductCategory
from app.models.pricing import CurrentPrice
from app.models.platform import Platform
from slowapi import Limiter
from slowapi.util import get_remote_address

# Set up logging
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


@router.get("/compare", response_model=ProductComparisonResponse)
@limiter.limit("20/minute")
async def compare_products(
    request: Request,
    product_name: str = Query(..., description="Product name to search for", min_length=1),
    platforms: Optional[str] = Query(None, description="Comma-separated platform names"),
    category: Optional[str] = Query(None, description="Product category filter"),
    brand: Optional[str] = Query(None, description="Brand filter"),
    db: Session = Depends(get_db)
):
    """
    Compare product prices across platforms.
    
    This endpoint searches for products by name and returns price comparisons
    across all available platforms or specified platforms.
    
    Parameters:
    - product_name: Name of the product to search for
    - platforms: Optional comma-separated list of platform names
    - category: Optional category filter
    - brand: Optional brand filter
    
    Returns detailed price comparison with best deals and savings potential.
    """
    start_time = time.time()
    
    try:
        # Validate and sanitize inputs
        validated_product_name = InputValidator.validate_product_name(product_name)
        
        validated_platforms = []
        if platforms:
            validated_platforms = InputValidator.validate_platform_list(platforms)
        
        validated_category = None
        if category:
            validated_category = InputValidator.validate_category_name(category)
        
        validated_brand = None
        if brand:
            validated_brand = InputValidator.sanitize_string(brand, max_length=100)
        
        logger.info(f"Comparing products for: {validated_product_name}")
        
        # Get product comparisons
        comparisons = await _get_product_comparisons(
            db, validated_product_name, validated_platforms, validated_category, validated_brand
        )
        
        # Check if no products found
        if not comparisons:
            raise ProductNotFoundError(
                validated_product_name,
                suggestions=[
                    "Try using more general product terms",
                    "Check product name spelling",
                    "Remove category or brand filters",
                    "Try without specifying platforms"
                ]
            )
        
        # Get list of platforms that were actually compared
        platforms_compared = list(set([
            price.platform_name 
            for comparison in comparisons 
            for price in comparison.platforms
        ]))
        
        execution_time = time.time() - start_time
        
        response = ProductComparisonResponse(
            query=validated_product_name,
            comparisons=comparisons,
            total_products=len(comparisons),
            platforms_compared=platforms_compared,
            execution_time=execution_time
        )
        
        logger.info(f"Product comparison completed in {execution_time:.2f}s, found {len(comparisons)} products")
        return response
        
    except ValidationError as e:
        logger.warning(f"Product comparison validation failed: {str(e)}")
        raise e
    except ProductNotFoundError as e:
        logger.info(f"No products found for comparison: {str(e)}")
        raise e
    except SQLAlchemyError as e:
        logger.error(f"Database error during product comparison: {str(e)}")
        raise DatabaseError(f"Database operation failed: {str(e)}", operation="product_comparison")
    except Exception as e:
        logger.error(f"Unexpected error during product comparison: {str(e)}")
        raise DatabaseError(f"Product comparison failed: {str(e)}", operation="product_comparison")


async def _get_product_comparisons(
    db: Session, 
    product_name: str, 
    platforms: List[str], 
    category: Optional[str], 
    brand: Optional[str]
) -> List[ProductComparison]:
    """Get product price comparisons across platforms"""
    
    try:
        # Build base query
        query = db.query(
            Product.id,
            Product.name,
            Product.description,
            Product.pack_size,
            Product.is_organic,
            ProductBrand.name.label('brand_name'),
            ProductCategory.name.label('category_name'),
            Platform.id.label('platform_id'),
            Platform.name.label('platform_name'),
            CurrentPrice.price,
            CurrentPrice.original_price,
            CurrentPrice.discount_percentage,
            CurrentPrice.is_available,
            CurrentPrice.stock_status,
            CurrentPrice.delivery_time_minutes,
            CurrentPrice.last_updated
        ).join(
            CurrentPrice, Product.id == CurrentPrice.product_id
        ).join(
            Platform, CurrentPrice.platform_id == Platform.id
        ).outerjoin(
            ProductBrand, Product.brand_id == ProductBrand.id
        ).outerjoin(
            ProductCategory, Product.category_id == ProductCategory.id
        ).filter(
            Product.name.ilike(f'%{product_name}%'),
            Product.is_active == True,
            Platform.is_active == True
        )
        
        # Apply filters
        if platforms:
            query = query.filter(Platform.name.in_(platforms))
        
        if category:
            query = query.filter(ProductCategory.name.ilike(f'%{category}%'))
        
        if brand:
            query = query.filter(ProductBrand.name.ilike(f'%{brand}%'))
        
        # Execute query
        rows = query.order_by(Product.name, CurrentPrice.price).all()
        
        # Group results by product
        products_dict = {}
        for row in rows:
            product_id = row.id
            
            if product_id not in products_dict:
                products_dict[product_id] = {
                    'product': ProductInfo(
                        id=row.id,
                        name=row.name,
                        brand=row.brand_name,
                        category=row.category_name,
                        description=row.description,
                        pack_size=row.pack_size,
                        is_organic=row.is_organic
                    ),
                    'platforms': []
                }
            
            # Add platform price data
            platform_price = ProductPrice(
                platform_id=row.platform_id,
                platform_name=row.platform_name,
                current_price=float(row.price),
                original_price=float(row.original_price) if row.original_price else None,
                discount_percentage=float(row.discount_percentage) if row.discount_percentage else None,
                is_available=row.is_available,
                stock_status=row.stock_status,
                delivery_time_minutes=row.delivery_time_minutes,
                last_updated=row.last_updated
            )
            
            products_dict[product_id]['platforms'].append(platform_price)
        
        # Convert to ProductComparison objects
        comparisons = []
        for product_data in products_dict.values():
            if product_data['platforms']:  # Only include products with price data
                
                # Find best deal (lowest price among available products)
                available_prices = [p for p in product_data['platforms'] if p.is_available]
                if available_prices:
                    best_deal = min(available_prices, key=lambda x: x.current_price)
                    
                    # Calculate price range and savings
                    prices = [p.current_price for p in available_prices]
                    min_price = min(prices)
                    max_price = max(prices)
                    savings_potential = max_price - min_price
                    
                    comparison = ProductComparison(
                        product=product_data['product'],
                        platforms=product_data['platforms'],
                        best_deal=best_deal,
                        savings_potential=savings_potential,
                        price_range={"min": min_price, "max": max_price}
                    )
                    
                    comparisons.append(comparison)
        
        return comparisons
        
    except Exception as e:
        logger.error(f"Error getting product comparisons: {str(e)}")
        raise


@router.post("/compare", response_model=ProductComparisonResponse)
@limiter.limit("20/minute")
async def compare_products_post(
    request: Request,
    comparison_request: ProductComparisonRequest,
    db: Session = Depends(get_db)
):
    """
    Compare product prices across platforms (POST version).
    
    This endpoint accepts a JSON request body with detailed comparison parameters.
    """
    start_time = time.time()
    
    try:
        # Validate and sanitize inputs
        validated_product_name = InputValidator.validate_product_name(comparison_request.product_name)
        
        validated_platforms = []
        if comparison_request.platforms:
            validated_platforms = InputValidator.validate_platform_list(comparison_request.platforms)
        
        validated_category = None
        if comparison_request.category:
            validated_category = InputValidator.validate_category_name(comparison_request.category)
        
        validated_brand = None
        if comparison_request.brand:
            validated_brand = InputValidator.sanitize_string(comparison_request.brand, max_length=100)
        
        logger.info(f"Comparing products for: {validated_product_name}")
        
        # Get product comparisons
        comparisons = await _get_product_comparisons(
            db, 
            validated_product_name, 
            validated_platforms, 
            validated_category, 
            validated_brand
        )
        
        # Check if no products found
        if not comparisons:
            raise ProductNotFoundError(
                validated_product_name,
                suggestions=[
                    "Try using more general product terms",
                    "Check product name spelling",
                    "Remove category or brand filters",
                    "Try without specifying platforms"
                ]
            )
        
        # Get list of platforms that were actually compared
        platforms_compared = list(set([
            price.platform_name 
            for comparison in comparisons 
            for price in comparison.platforms
        ]))
        
        execution_time = time.time() - start_time
        
        response = ProductComparisonResponse(
            query=validated_product_name,
            comparisons=comparisons,
            total_products=len(comparisons),
            platforms_compared=platforms_compared,
            execution_time=execution_time
        )
        
        logger.info(f"Product comparison completed in {execution_time:.2f}s, found {len(comparisons)} products")
        return response
        
    except ValidationError as e:
        logger.warning(f"Product comparison validation failed: {str(e)}")
        raise e
    except ProductNotFoundError as e:
        logger.info(f"No products found for comparison: {str(e)}")
        raise e
    except SQLAlchemyError as e:
        logger.error(f"Database error during product comparison: {str(e)}")
        raise DatabaseError(f"Database operation failed: {str(e)}", operation="product_comparison")
    except Exception as e:
        logger.error(f"Unexpected error during product comparison: {str(e)}")
        raise DatabaseError(f"Product comparison failed: {str(e)}", operation="product_comparison")