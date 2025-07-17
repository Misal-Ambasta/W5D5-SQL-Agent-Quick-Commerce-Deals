"""
Deals and discounts endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Dict, Any
import time
import logging
from datetime import datetime

from app.core.dependencies import get_db
from app.core.validation import InputValidator
from app.core.exceptions import (
    ValidationError,
    DatabaseError,
    PlatformNotFoundError
)
from app.schemas.deals import DealsRequest, DealsResponse, DealInfo, CampaignInfo
from app.models.product import Product, ProductCategory
from app.models.pricing import Discount, PromotionalCampaign, CurrentPrice
from app.models.platform import Platform
from slowapi import Limiter
from slowapi.util import get_remote_address

# Set up logging
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


@router.get("/", response_model=DealsResponse)
@limiter.limit("30/minute")
async def get_deals(
    request: Request,
    platform: Optional[str] = Query(None, description="Filter by platform name"),
    category: Optional[str] = Query(None, description="Filter by product category"),
    min_discount: Optional[float] = Query(0, description="Minimum discount percentage", ge=0, le=100),
    max_discount: Optional[float] = Query(None, description="Maximum discount percentage", ge=0, le=100),
    featured_only: Optional[bool] = Query(False, description="Show only featured deals"),
    active_only: Optional[bool] = Query(True, description="Show only currently active deals"),
    limit: Optional[int] = Query(50, description="Maximum number of deals to return", ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get current deals and discounts.
    
    This endpoint returns active deals and discounts across platforms with
    various filtering options.
    
    Parameters:
    - platform: Filter by specific platform name
    - category: Filter by product category
    - min_discount: Minimum discount percentage (0-100)
    - max_discount: Maximum discount percentage (0-100)
    - featured_only: Show only featured deals
    - active_only: Show only currently active deals
    - limit: Maximum number of deals to return (1-100)
    
    Returns list of deals with detailed information including savings and terms.
    """
    start_time = time.time()
    
    try:
        # Validate and sanitize inputs
        validated_platform = None
        if platform:
            validated_platform = InputValidator.validate_platform_name(platform)
        
        validated_category = None
        if category:
            validated_category = InputValidator.validate_category_name(category)
        
        validated_min_discount = InputValidator.validate_discount_percentage(min_discount)
        
        validated_max_discount = None
        if max_discount is not None:
            validated_max_discount = InputValidator.validate_discount_percentage(max_discount)
        
        validated_limit = InputValidator.validate_limit(limit)
        
        # Validate discount range
        if validated_max_discount is not None and validated_min_discount > validated_max_discount:
            raise ValidationError("Minimum discount cannot be greater than maximum discount")
        
        logger.info(f"Fetching deals with filters: platform={validated_platform}, category={validated_category}, min_discount={validated_min_discount}")
        
        # Create filters dict for response
        filters_applied = {
            "platform": validated_platform,
            "category": validated_category,
            "min_discount": validated_min_discount,
            "max_discount": validated_max_discount,
            "featured_only": featured_only,
            "active_only": active_only,
            "limit": validated_limit
        }
        
        # Get deals
        deals = await _get_deals_list(
            db, validated_platform, validated_category, validated_min_discount, validated_max_discount, 
            featured_only, active_only, validated_limit
        )
        
        # Get unique platforms and categories from results
        platforms_included = list(set([deal.platform_name for deal in deals]))
        categories_included = list(set([deal.category_name for deal in deals if deal.category_name]))
        
        execution_time = time.time() - start_time
        
        response = DealsResponse(
            deals=deals,
            total_deals=len(deals),
            filters_applied=filters_applied,
            platforms_included=platforms_included,
            categories_included=categories_included,
            execution_time=execution_time
        )
        
        logger.info(f"Deals fetched successfully in {execution_time:.2f}s, returned {len(deals)} deals")
        return response
        
    except ValidationError as e:
        logger.warning(f"Deals validation failed: {str(e)}")
        raise e
    except SQLAlchemyError as e:
        logger.error(f"Database error during deals fetching: {str(e)}")
        raise DatabaseError(f"Database operation failed: {str(e)}", operation="deals_fetching")
    except Exception as e:
        logger.error(f"Unexpected error during deals fetching: {str(e)}")
        raise DatabaseError(f"Deals fetching failed: {str(e)}", operation="deals_fetching")


@router.post("/", response_model=DealsResponse)
@limiter.limit("30/minute")
async def get_deals_post(
    request: Request,
    deals_request: DealsRequest,
    db: Session = Depends(get_db)
):
    """
    Get current deals and discounts (POST version).
    
    This endpoint accepts a JSON request body with detailed filtering parameters.
    """
    start_time = time.time()
    
    try:
        # Validate and sanitize inputs from request body
        validated_platform = None
        if deals_request.platform:
            validated_platform = InputValidator.validate_platform_name(deals_request.platform)
        
        validated_category = None
        if deals_request.category:
            validated_category = InputValidator.validate_category_name(deals_request.category)
        
        validated_min_discount = InputValidator.validate_discount_percentage(deals_request.min_discount or 0)
        
        validated_max_discount = None
        if deals_request.max_discount is not None:
            validated_max_discount = InputValidator.validate_discount_percentage(deals_request.max_discount)
        
        validated_limit = InputValidator.validate_limit(deals_request.limit or 50)
        
        # Validate discount range
        if validated_max_discount is not None and validated_min_discount > validated_max_discount:
            raise ValidationError("Minimum discount cannot be greater than maximum discount")
        
        logger.info(f"Fetching deals with validated request: platform={validated_platform}, category={validated_category}")
        
        # Get deals
        deals = await _get_deals_list(
            db, 
            validated_platform,
            validated_category,
            validated_min_discount,
            validated_max_discount,
            deals_request.featured_only,
            deals_request.active_only,
            validated_limit
        )
        
        # Get unique platforms and categories from results
        platforms_included = list(set([deal.platform_name for deal in deals]))
        categories_included = list(set([deal.category_name for deal in deals if deal.category_name]))
        
        execution_time = time.time() - start_time
        
        # Create filters dict with validated values
        filters_applied = {
            "platform": validated_platform,
            "category": validated_category,
            "min_discount": validated_min_discount,
            "max_discount": validated_max_discount,
            "featured_only": deals_request.featured_only,
            "active_only": deals_request.active_only,
            "limit": validated_limit
        }
        
        response = DealsResponse(
            deals=deals,
            total_deals=len(deals),
            filters_applied=filters_applied,
            platforms_included=platforms_included,
            categories_included=categories_included,
            execution_time=execution_time
        )
        
        logger.info(f"Deals fetched successfully in {execution_time:.2f}s, returned {len(deals)} deals")
        return response
        
    except ValidationError as e:
        logger.warning(f"Deals validation failed: {str(e)}")
        raise e
    except SQLAlchemyError as e:
        logger.error(f"Database error during deals fetching: {str(e)}")
        raise DatabaseError(f"Database operation failed: {str(e)}", operation="deals_fetching")
    except Exception as e:
        logger.error(f"Unexpected error during deals fetching: {str(e)}")
        raise DatabaseError(f"Deals fetching failed: {str(e)}", operation="deals_fetching")


async def _get_deals_list(
    db: Session,
    platform: Optional[str],
    category: Optional[str],
    min_discount: Optional[float],
    max_discount: Optional[float],
    featured_only: Optional[bool],
    active_only: Optional[bool],
    limit: Optional[int]
) -> List[DealInfo]:
    """Get list of deals based on filters"""
    
    try:
        current_time = datetime.utcnow()
        
        # Build base query for discounts
        query = db.query(
            Discount.id,
            Discount.title,
            Discount.description,
            Discount.discount_type,
            Discount.discount_value,
            Discount.discount_percentage,
            Discount.max_discount_amount,
            Discount.min_order_amount,
            Discount.discount_code,
            Discount.is_featured,
            Discount.start_date,
            Discount.end_date,
            Discount.usage_limit_per_user,
            Platform.name.label('platform_name'),
            Product.name.label('product_name'),
            ProductCategory.name.label('category_name'),
            CurrentPrice.price.label('current_price'),
            CurrentPrice.original_price
        ).join(
            Platform, Discount.platform_id == Platform.id
        ).outerjoin(
            Product, Discount.product_id == Product.id
        ).outerjoin(
            ProductCategory, Discount.category_id == ProductCategory.id
        ).outerjoin(
            CurrentPrice, and_(
                CurrentPrice.product_id == Product.id,
                CurrentPrice.platform_id == Platform.id
            )
        ).filter(
            Platform.is_active == True
        )
        
        # Apply active filter
        if active_only:
            query = query.filter(
                and_(
                    Discount.is_active == True,
                    Discount.start_date <= current_time,
                    Discount.end_date >= current_time
                )
            )
        
        # Apply platform filter
        if platform:
            query = query.filter(Platform.name.ilike(f'%{platform}%'))
        
        # Apply category filter
        if category:
            query = query.filter(ProductCategory.name.ilike(f'%{category}%'))
        
        # Apply discount filters
        if min_discount is not None and min_discount > 0:
            query = query.filter(Discount.discount_percentage >= min_discount)
        
        if max_discount is not None:
            query = query.filter(Discount.discount_percentage <= max_discount)
        
        # Apply featured filter
        if featured_only:
            query = query.filter(Discount.is_featured == True)
        
        # Apply limit and ordering
        query = query.order_by(
            Discount.is_featured.desc(),
            Discount.discount_percentage.desc(),
            Discount.start_date.desc()
        )
        
        if limit:
            query = query.limit(limit)
        
        # Execute query
        rows = query.all()
        
        # Convert to DealInfo objects
        deals = []
        for row in rows:
            # Calculate discounted price and savings if we have price data
            discounted_price = None
            savings_amount = None
            
            if row.current_price and row.discount_percentage:
                current_price = float(row.current_price)
                discount_pct = float(row.discount_percentage)
                discounted_price = current_price * (1 - discount_pct / 100)
                savings_amount = current_price - discounted_price
            elif row.original_price and row.current_price:
                savings_amount = float(row.original_price) - float(row.current_price)
                discounted_price = float(row.current_price)
            
            deal = DealInfo(
                id=row.id,
                title=row.title,
                description=row.description,
                discount_type=row.discount_type,
                discount_value=float(row.discount_value),
                discount_percentage=float(row.discount_percentage) if row.discount_percentage else None,
                max_discount_amount=float(row.max_discount_amount) if row.max_discount_amount else None,
                min_order_amount=float(row.min_order_amount) if row.min_order_amount else None,
                discount_code=row.discount_code,
                platform_name=row.platform_name,
                product_name=row.product_name,
                category_name=row.category_name,
                original_price=float(row.original_price) if row.original_price else None,
                discounted_price=discounted_price,
                savings_amount=savings_amount,
                is_featured=row.is_featured,
                start_date=row.start_date,
                end_date=row.end_date,
                usage_limit_per_user=row.usage_limit_per_user
            )
            
            deals.append(deal)
        
        return deals
        
    except Exception as e:
        logger.error(f"Error getting deals list: {str(e)}")
        raise


@router.get("/campaigns", response_model=List[CampaignInfo])
@limiter.limit("20/minute")
async def get_promotional_campaigns(
    request: Request,
    platform: Optional[str] = Query(None, description="Filter by platform name"),
    campaign_type: Optional[str] = Query(None, description="Filter by campaign type"),
    featured_only: Optional[bool] = Query(False, description="Show only featured campaigns"),
    active_only: Optional[bool] = Query(True, description="Show only currently active campaigns"),
    limit: Optional[int] = Query(20, description="Maximum number of campaigns to return", ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get promotional campaigns.
    
    This endpoint returns active promotional campaigns across platforms.
    """
    start_time = time.time()
    
    try:
        # Validate and sanitize inputs
        validated_platform = None
        if platform:
            validated_platform = InputValidator.validate_platform_name(platform)
        
        validated_campaign_type = None
        if campaign_type:
            validated_campaign_type = InputValidator.sanitize_string(campaign_type, max_length=100)
        
        validated_limit = InputValidator.validate_limit(limit)
        
        logger.info(f"Fetching campaigns with filters: platform={validated_platform}, type={validated_campaign_type}")
        
        current_time = datetime.utcnow()
        
        # Build query
        query = db.query(
            PromotionalCampaign.id,
            PromotionalCampaign.campaign_name,
            PromotionalCampaign.campaign_type,
            PromotionalCampaign.description,
            PromotionalCampaign.banner_image_url,
            PromotionalCampaign.min_order_amount,
            PromotionalCampaign.max_discount_amount,
            PromotionalCampaign.is_featured,
            PromotionalCampaign.start_date,
            PromotionalCampaign.end_date,
            Platform.name.label('platform_name')
        ).join(
            Platform, PromotionalCampaign.platform_id == Platform.id
        ).filter(
            Platform.is_active == True
        )
        
        # Apply filters
        if active_only:
            query = query.filter(
                and_(
                    PromotionalCampaign.is_active == True,
                    PromotionalCampaign.start_date <= current_time,
                    PromotionalCampaign.end_date >= current_time
                )
            )
        
        if validated_platform:
            query = query.filter(Platform.name.ilike(f'%{validated_platform}%'))
        
        if validated_campaign_type:
            query = query.filter(PromotionalCampaign.campaign_type.ilike(f'%{validated_campaign_type}%'))
        
        if featured_only:
            query = query.filter(PromotionalCampaign.is_featured == True)
        
        # Apply ordering and limit
        query = query.order_by(
            PromotionalCampaign.is_featured.desc(),
            PromotionalCampaign.start_date.desc()
        )
        
        if validated_limit:
            query = query.limit(validated_limit)
        
        rows = query.all()
        
        # Convert to CampaignInfo objects
        campaigns = []
        for row in rows:
            campaign = CampaignInfo(
                id=row.id,
                campaign_name=row.campaign_name,
                campaign_type=row.campaign_type,
                description=row.description,
                platform_name=row.platform_name,
                banner_image_url=row.banner_image_url,
                min_order_amount=float(row.min_order_amount) if row.min_order_amount else None,
                max_discount_amount=float(row.max_discount_amount) if row.max_discount_amount else None,
                is_featured=row.is_featured,
                start_date=row.start_date,
                end_date=row.end_date,
                products_count=0  # This would need a separate query to count products
            )
            campaigns.append(campaign)
        
        execution_time = time.time() - start_time
        logger.info(f"Campaigns fetched successfully in {execution_time:.2f}s, returned {len(campaigns)} campaigns")
        
        return campaigns
        
    except ValidationError as e:
        logger.warning(f"Campaigns validation failed: {str(e)}")
        raise e
    except SQLAlchemyError as e:
        logger.error(f"Database error during campaigns fetching: {str(e)}")
        raise DatabaseError(f"Database operation failed: {str(e)}", operation="campaigns_fetching")
    except Exception as e:
        logger.error(f"Unexpected error during campaigns fetching: {str(e)}")
        raise DatabaseError(f"Campaigns fetching failed: {str(e)}", operation="campaigns_fetching")