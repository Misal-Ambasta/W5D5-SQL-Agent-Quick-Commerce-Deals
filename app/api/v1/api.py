"""
API v1 router configuration
"""
from fastapi import APIRouter

from app.api.v1.endpoints import query, products, deals
from app.api.v1 import monitoring

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(query.router, prefix="/query", tags=["query"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(deals.router, prefix="/deals", tags=["deals"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])