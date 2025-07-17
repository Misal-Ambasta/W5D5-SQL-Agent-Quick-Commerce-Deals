"""
Pydantic schemas for product comparison endpoints
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class ProductPrice(BaseModel):
    """Product price information for a specific platform"""
    platform_id: int
    platform_name: str
    current_price: float
    original_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    is_available: bool
    stock_status: str
    delivery_time_minutes: Optional[int] = None
    last_updated: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "platform_id": 1,
                "platform_name": "Blinkit",
                "current_price": 45.00,
                "original_price": 50.00,
                "discount_percentage": 10.0,
                "is_available": True,
                "stock_status": "in_stock",
                "delivery_time_minutes": 15,
                "last_updated": "2024-01-15T10:30:00Z"
            }
        }


class ProductInfo(BaseModel):
    """Basic product information"""
    id: int
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    pack_size: Optional[str] = None
    is_organic: bool = False
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Red Onions",
                "brand": "Fresh Farm",
                "category": "Vegetables",
                "description": "Fresh red onions",
                "pack_size": "1kg",
                "is_organic": False
            }
        }


class ProductComparison(BaseModel):
    """Product comparison across platforms"""
    product: ProductInfo
    platforms: List[ProductPrice]
    best_deal: ProductPrice
    savings_potential: float = Field(..., description="Maximum savings compared to highest price")
    price_range: Dict[str, float] = Field(..., description="Min and max prices across platforms")
    
    class Config:
        schema_extra = {
            "example": {
                "product": {
                    "id": 1,
                    "name": "Red Onions",
                    "brand": "Fresh Farm",
                    "category": "Vegetables",
                    "description": "Fresh red onions",
                    "pack_size": "1kg",
                    "is_organic": False
                },
                "platforms": [
                    {
                        "platform_id": 1,
                        "platform_name": "Blinkit",
                        "current_price": 45.00,
                        "original_price": 50.00,
                        "discount_percentage": 10.0,
                        "is_available": True,
                        "stock_status": "in_stock",
                        "delivery_time_minutes": 15,
                        "last_updated": "2024-01-15T10:30:00Z"
                    }
                ],
                "best_deal": {
                    "platform_id": 1,
                    "platform_name": "Blinkit",
                    "current_price": 45.00,
                    "original_price": 50.00,
                    "discount_percentage": 10.0,
                    "is_available": True,
                    "stock_status": "in_stock",
                    "delivery_time_minutes": 15,
                    "last_updated": "2024-01-15T10:30:00Z"
                },
                "savings_potential": 5.00,
                "price_range": {"min": 45.00, "max": 50.00}
            }
        }


class ProductComparisonRequest(BaseModel):
    """Request model for product comparison"""
    product_name: str = Field(..., description="Product name to search for", min_length=1, max_length=255)
    platforms: Optional[List[str]] = Field(None, description="Specific platforms to compare (optional)")
    category: Optional[str] = Field(None, description="Product category filter")
    brand: Optional[str] = Field(None, description="Brand filter")
    
    class Config:
        schema_extra = {
            "example": {
                "product_name": "onions",
                "platforms": ["Blinkit", "Zepto", "Instamart"],
                "category": "Vegetables"
            }
        }


class ProductComparisonResponse(BaseModel):
    """Response model for product comparison"""
    query: str
    comparisons: List[ProductComparison]
    total_products: int
    platforms_compared: List[str]
    execution_time: float
    
    class Config:
        schema_extra = {
            "example": {
                "query": "onions",
                "comparisons": [
                    {
                        "product": {
                            "id": 1,
                            "name": "Red Onions",
                            "brand": "Fresh Farm",
                            "category": "Vegetables",
                            "description": "Fresh red onions",
                            "pack_size": "1kg",
                            "is_organic": False
                        },
                        "platforms": [],
                        "best_deal": {},
                        "savings_potential": 5.00,
                        "price_range": {"min": 45.00, "max": 50.00}
                    }
                ],
                "total_products": 1,
                "platforms_compared": ["Blinkit", "Zepto"],
                "execution_time": 0.15
            }
        }