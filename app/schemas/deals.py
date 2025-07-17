"""
Pydantic schemas for deals and discounts endpoints
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DealInfo(BaseModel):
    """Individual deal information"""
    id: int
    title: str
    description: Optional[str] = None
    discount_type: str = Field(..., description="Type of discount: percentage, fixed_amount, buy_x_get_y")
    discount_value: float
    discount_percentage: Optional[float] = None
    max_discount_amount: Optional[float] = None
    min_order_amount: Optional[float] = None
    discount_code: Optional[str] = None
    platform_name: str
    product_name: Optional[str] = None
    category_name: Optional[str] = None
    original_price: Optional[float] = None
    discounted_price: Optional[float] = None
    savings_amount: Optional[float] = None
    is_featured: bool = False
    start_date: datetime
    end_date: datetime
    usage_limit_per_user: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "title": "30% off on Fresh Vegetables",
                "description": "Get 30% discount on all fresh vegetables",
                "discount_type": "percentage",
                "discount_value": 30.0,
                "discount_percentage": 30.0,
                "max_discount_amount": 100.0,
                "min_order_amount": 200.0,
                "discount_code": "VEGGIE30",
                "platform_name": "Blinkit",
                "product_name": "Red Onions",
                "category_name": "Vegetables",
                "original_price": 50.0,
                "discounted_price": 35.0,
                "savings_amount": 15.0,
                "is_featured": True,
                "start_date": "2024-01-15T00:00:00Z",
                "end_date": "2024-01-20T23:59:59Z",
                "usage_limit_per_user": 5
            }
        }


class DealsRequest(BaseModel):
    """Request model for deals endpoint"""
    platform: Optional[str] = Field(None, description="Filter by platform name")
    category: Optional[str] = Field(None, description="Filter by product category")
    min_discount: Optional[float] = Field(0, description="Minimum discount percentage", ge=0, le=100)
    max_discount: Optional[float] = Field(None, description="Maximum discount percentage", ge=0, le=100)
    featured_only: Optional[bool] = Field(False, description="Show only featured deals")
    active_only: Optional[bool] = Field(True, description="Show only currently active deals")
    limit: Optional[int] = Field(50, description="Maximum number of deals to return", ge=1, le=100)
    
    class Config:
        schema_extra = {
            "example": {
                "platform": "Blinkit",
                "category": "Vegetables",
                "min_discount": 30.0,
                "featured_only": True,
                "limit": 20
            }
        }


class DealsResponse(BaseModel):
    """Response model for deals endpoint"""
    deals: List[DealInfo]
    total_deals: int
    filters_applied: Dict[str, Any]
    platforms_included: List[str]
    categories_included: List[str]
    execution_time: float
    
    class Config:
        schema_extra = {
            "example": {
                "deals": [
                    {
                        "id": 1,
                        "title": "30% off on Fresh Vegetables",
                        "description": "Get 30% discount on all fresh vegetables",
                        "discount_type": "percentage",
                        "discount_value": 30.0,
                        "discount_percentage": 30.0,
                        "max_discount_amount": 100.0,
                        "min_order_amount": 200.0,
                        "discount_code": "VEGGIE30",
                        "platform_name": "Blinkit",
                        "product_name": "Red Onions",
                        "category_name": "Vegetables",
                        "original_price": 50.0,
                        "discounted_price": 35.0,
                        "savings_amount": 15.0,
                        "is_featured": True,
                        "start_date": "2024-01-15T00:00:00Z",
                        "end_date": "2024-01-20T23:59:59Z",
                        "usage_limit_per_user": 5
                    }
                ],
                "total_deals": 1,
                "filters_applied": {
                    "platform": "Blinkit",
                    "min_discount": 30.0,
                    "featured_only": True
                },
                "platforms_included": ["Blinkit"],
                "categories_included": ["Vegetables"],
                "execution_time": 0.12
            }
        }


class CampaignInfo(BaseModel):
    """Promotional campaign information"""
    id: int
    campaign_name: str
    campaign_type: str
    description: Optional[str] = None
    platform_name: str
    banner_image_url: Optional[str] = None
    min_order_amount: Optional[float] = None
    max_discount_amount: Optional[float] = None
    is_featured: bool = False
    start_date: datetime
    end_date: datetime
    products_count: int = 0
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "campaign_name": "Flash Sale Friday",
                "campaign_type": "flash_sale",
                "description": "Limited time flash sale on selected items",
                "platform_name": "Blinkit",
                "banner_image_url": "https://example.com/banner.jpg",
                "min_order_amount": 500.0,
                "max_discount_amount": 200.0,
                "is_featured": True,
                "start_date": "2024-01-15T00:00:00Z",
                "end_date": "2024-01-15T23:59:59Z",
                "products_count": 25
            }
        }