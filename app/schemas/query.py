"""
Pydantic schemas for natural language query endpoints
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class NaturalLanguageQuery(BaseModel):
    """Request model for natural language queries"""
    query: str = Field(..., description="Natural language query", min_length=1, max_length=500)
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the query")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Which app has cheapest onions right now?",
                "user_id": "user123",
                "context": {"location": "Mumbai"}
            }
        }


class QueryResult(BaseModel):
    """Individual query result item"""
    product_id: int
    product_name: str
    platform_name: str
    current_price: float
    original_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    is_available: bool
    last_updated: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "product_id": 1,
                "product_name": "Red Onions (1kg)",
                "platform_name": "Blinkit",
                "current_price": 45.00,
                "original_price": 50.00,
                "discount_percentage": 10.0,
                "is_available": True,
                "last_updated": "2024-01-15T10:30:00Z"
            }
        }


class QueryResponse(BaseModel):
    """Response model for natural language queries"""
    query: str
    results: List[QueryResult]
    execution_time: float = Field(..., description="Query execution time in seconds")
    relevant_tables: List[str] = Field(..., description="Database tables used in the query")
    total_results: int
    cached: bool = Field(False, description="Whether the result was served from cache")
    suggestions: Optional[List[str]] = Field(None, description="Query suggestions if no results found")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for advanced queries")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Which app has cheapest onions right now?",
                "results": [
                    {
                        "product_id": 1,
                        "product_name": "Red Onions (1kg)",
                        "platform_name": "Blinkit",
                        "current_price": 45.00,
                        "original_price": 50.00,
                        "discount_percentage": 10.0,
                        "is_available": True,
                        "last_updated": "2024-01-15T10:30:00Z"
                    }
                ],
                "execution_time": 0.25,
                "relevant_tables": ["products", "current_prices", "platforms"],
                "total_results": 1,
                "cached": False
            }
        }


class QueryError(BaseModel):
    """Error response model for query failures"""
    error: str
    message: str
    suggestions: Optional[List[str]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "error": "Query Processing Failed",
                "message": "Unable to understand the query",
                "suggestions": [
                    "Try rephrasing your query",
                    "Use more specific product names",
                    "Check spelling and grammar"
                ]
            }
        }