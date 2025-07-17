"""
Sample Query Handlers for Quick Commerce Deals platform.
Implements specific sample queries as required in task 8.1.
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timedelta
import re

from app.models.product import Product, ProductCategory
from app.models.pricing import CurrentPrice, Discount
from app.models.platform import Platform
from app.schemas.query import QueryResult

logger = logging.getLogger(__name__)


class SampleQueryHandlers:
    """
    Handlers for specific sample queries as defined in requirements 10.1-10.4.
    """
    
    def __init__(self):
        """Initialize the sample query handlers."""
        self.common_products = {
            'onions': ['onion', 'onions', 'red onion', 'white onion', 'yellow onion'],
            'tomatoes': ['tomato', 'tomatoes', 'cherry tomato', 'roma tomato'],
            'potatoes': ['potato', 'potatoes', 'aloo'],
            'apples': ['apple', 'apples', 'red apple', 'green apple'],
            'bananas': ['banana', 'bananas', 'kela'],
            'milk': ['milk', 'dairy milk', 'toned milk', 'full cream milk'],
            'bread': ['bread', 'white bread', 'brown bread', 'whole wheat bread'],
            'rice': ['rice', 'basmati rice', 'jasmine rice', 'brown rice'],
            'fruits': ['apple', 'banana', 'orange', 'mango', 'grapes', 'strawberry', 'kiwi', 'pineapple']
        }
        
        self.platform_mappings = {
            'blinkit': ['blinkit', 'grofers'],
            'zepto': ['zepto'],
            'instamart': ['instamart', 'swiggy instamart'],
            'bigbasket': ['bigbasket', 'bigbasket now', 'bb now'],
            'swiggy': ['swiggy', 'swiggy instamart']
        }
    
    async def handle_cheapest_product_query(
        self, 
        db: Session, 
        query: str
    ) -> List[QueryResult]:
        """
        Handle "Which app has cheapest [product] right now?" queries.
        Requirement: 10.1
        """
        logger.info(f"Processing cheapest product query: {query}")
        
        try:
            # Extract product name from query
            product_name = self._extract_product_name(query)
            if not product_name:
                logger.warning("Could not extract product name from query")
                return []
            
            logger.info(f"Searching for cheapest '{product_name}'")
            
            # Find products matching the name
            product_variations = self._get_product_variations(product_name)
            
            # Query for cheapest prices across all platforms
            cheapest_query = db.query(
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
                and_(
                    or_(*[Product.name.ilike(f'%{variation}%') for variation in product_variations]),
                    CurrentPrice.is_available == True,
                    Platform.is_active == True,
                    Product.is_active == True
                )
            ).order_by(
                CurrentPrice.price.asc()
            ).limit(10)
            
            rows = cheapest_query.all()
            
            if not rows:
                logger.info(f"No results found for product: {product_name}")
                return []
            
            # Convert to QueryResult objects
            results = []
            for row in rows:
                result = QueryResult(
                    product_id=row.id,
                    product_name=row.name,
                    platform_name=row.platform_name,
                    current_price=float(row.price),
                    original_price=float(row.original_price) if row.original_price else None,
                    discount_percentage=float(row.discount_percentage) if row.discount_percentage else None,
                    is_available=row.is_available,
                    last_updated=row.last_updated
                )
                results.append(result)
            
            logger.info(f"Found {len(results)} cheapest options for '{product_name}'")
            return results
            
        except Exception as e:
            logger.error(f"Error processing cheapest product query: {str(e)}")
            return []
    
    async def handle_discount_query(
        self, 
        db: Session, 
        query: str
    ) -> List[QueryResult]:
        """
        Handle "Show products with X%+ discount on [platform]" queries.
        Requirement: 10.2
        """
        logger.info(f"Processing discount query: {query}")
        
        try:
            # Extract discount percentage and platform
            min_discount = self._extract_discount_percentage(query)
            platform_name = self._extract_platform_name(query)
            
            if min_discount == 0:
                logger.warning("Could not extract discount percentage from query")
                return []
            
            logger.info(f"Searching for products with {min_discount}%+ discount on {platform_name or 'all platforms'}")
            
            # Build query for discounted products
            discount_query = db.query(
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
                and_(
                    CurrentPrice.discount_percentage >= min_discount,
                    CurrentPrice.is_available == True,
                    Platform.is_active == True,
                    Product.is_active == True,
                    CurrentPrice.original_price.isnot(None)  # Must have original price to calculate discount
                )
            )
            
            # Filter by platform if specified
            if platform_name:
                platform_variations = self._get_platform_variations(platform_name)
                discount_query = discount_query.filter(
                    or_(*[Platform.name.ilike(f'%{variation}%') for variation in platform_variations])
                )
            
            # Order by discount percentage (highest first)
            discount_query = discount_query.order_by(
                desc(CurrentPrice.discount_percentage),
                asc(CurrentPrice.price)
            ).limit(50)
            
            rows = discount_query.all()
            
            if not rows:
                logger.info(f"No products found with {min_discount}%+ discount")
                return []
            
            # Convert to QueryResult objects
            results = []
            for row in rows:
                result = QueryResult(
                    product_id=row.id,
                    product_name=row.name,
                    platform_name=row.platform_name,
                    current_price=float(row.price),
                    original_price=float(row.original_price) if row.original_price else None,
                    discount_percentage=float(row.discount_percentage) if row.discount_percentage else None,
                    is_available=row.is_available,
                    last_updated=row.last_updated
                )
                results.append(result)
            
            logger.info(f"Found {len(results)} products with {min_discount}%+ discount")
            return results
            
        except Exception as e:
            logger.error(f"Error processing discount query: {str(e)}")
            return []
    
    async def handle_price_comparison_query(
        self, 
        db: Session, 
        query: str
    ) -> List[QueryResult]:
        """
        Handle "Compare [product/category] prices between [platform1] and [platform2]" queries.
        Requirement: 10.3
        """
        logger.info(f"Processing price comparison query: {query}")
        
        try:
            # Extract product/category and platforms
            product_name = self._extract_product_name(query)
            platforms = self._extract_platforms_for_comparison(query)
            
            if not product_name or len(platforms) < 2:
                logger.warning("Could not extract sufficient information for comparison")
                return []
            
            logger.info(f"Comparing '{product_name}' prices between {platforms}")
            
            # Get product variations
            product_variations = self._get_product_variations(product_name)
            platform_variations = []
            for platform in platforms:
                platform_variations.extend(self._get_platform_variations(platform))
            
            # Query for products on specified platforms
            comparison_query = db.query(
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
                and_(
                    or_(*[Product.name.ilike(f'%{variation}%') for variation in product_variations]),
                    or_(*[Platform.name.ilike(f'%{variation}%') for variation in platform_variations]),
                    CurrentPrice.is_available == True,
                    Platform.is_active == True,
                    Product.is_active == True
                )
            ).order_by(
                Product.name.asc(),
                CurrentPrice.price.asc()
            ).limit(100)
            
            rows = comparison_query.all()
            
            if not rows:
                logger.info(f"No products found for comparison between {platforms}")
                return []
            
            # Group results by product for better comparison
            product_groups = {}
            for row in rows:
                product_key = row.name.lower()
                if product_key not in product_groups:
                    product_groups[product_key] = []
                
                result = QueryResult(
                    product_id=row.id,
                    product_name=row.name,
                    platform_name=row.platform_name,
                    current_price=float(row.price),
                    original_price=float(row.original_price) if row.original_price else None,
                    discount_percentage=float(row.discount_percentage) if row.discount_percentage else None,
                    is_available=row.is_available,
                    last_updated=row.last_updated
                )
                product_groups[product_key].append(result)
            
            # Flatten results, prioritizing products available on multiple platforms
            results = []
            for product_key, product_results in product_groups.items():
                # Sort by platform count (products available on more platforms first)
                platform_count = len(set(r.platform_name for r in product_results))
                if platform_count >= 2:  # Available on at least 2 platforms
                    results.extend(sorted(product_results, key=lambda x: x.current_price))
            
            # If no multi-platform products, include all results
            if not results:
                for product_results in product_groups.values():
                    results.extend(sorted(product_results, key=lambda x: x.current_price))
            
            logger.info(f"Found {len(results)} products for price comparison")
            return results[:50]  # Limit to 50 results
            
        except Exception as e:
            logger.error(f"Error processing price comparison query: {str(e)}")
            return []
    
    async def handle_budget_optimization_query(
        self, 
        db: Session, 
        query: str
    ) -> List[QueryResult]:
        """
        Handle "Find best deals for ₹X grocery list" queries.
        Requirement: 10.4
        """
        logger.info(f"Processing budget optimization query: {query}")
        
        try:
            # Extract budget amount
            budget = self._extract_budget_amount(query)
            if budget <= 0:
                logger.warning("Could not extract valid budget amount from query")
                return []
            
            logger.info(f"Finding best deals within ₹{budget} budget")
            
            # Get essential grocery categories
            essential_categories = [
                'vegetables', 'fruits', 'dairy', 'grains', 'pulses', 
                'cooking oil', 'spices', 'bread', 'eggs'
            ]
            
            # Query for best deals across essential categories
            deals_query = db.query(
                Product.id,
                Product.name,
                Platform.name.label('platform_name'),
                CurrentPrice.price,
                CurrentPrice.original_price,
                CurrentPrice.discount_percentage,
                CurrentPrice.is_available,
                CurrentPrice.last_updated,
                ProductCategory.name.label('category_name')
            ).join(
                CurrentPrice, Product.id == CurrentPrice.product_id
            ).join(
                Platform, CurrentPrice.platform_id == Platform.id
            ).join(
                ProductCategory, Product.category_id == ProductCategory.id
            ).filter(
                and_(
                    CurrentPrice.is_available == True,
                    Platform.is_active == True,
                    Product.is_active == True,
                    CurrentPrice.price <= budget * 0.3,  # Individual items shouldn't exceed 30% of budget
                    or_(
                        CurrentPrice.discount_percentage >= 10,  # At least 10% discount
                        CurrentPrice.price <= 100  # Or very affordable items
                    )
                )
            ).order_by(
                desc(CurrentPrice.discount_percentage),
                asc(CurrentPrice.price)
            ).limit(100)
            
            rows = deals_query.all()
            
            if not rows:
                logger.info(f"No deals found within ₹{budget} budget")
                return []
            
            # Optimize selection for budget
            selected_items = self._optimize_grocery_selection(rows, budget)
            
            # Convert to QueryResult objects
            results = []
            total_cost = 0
            
            for row in selected_items:
                result = QueryResult(
                    product_id=row.id,
                    product_name=row.name,
                    platform_name=row.platform_name,
                    current_price=float(row.price),
                    original_price=float(row.original_price) if row.original_price else None,
                    discount_percentage=float(row.discount_percentage) if row.discount_percentage else None,
                    is_available=row.is_available,
                    last_updated=row.last_updated
                )
                results.append(result)
                total_cost += float(row.price)
            
            logger.info(f"Optimized grocery list: {len(results)} items for ₹{total_cost:.2f} (budget: ₹{budget})")
            return results
            
        except Exception as e:
            logger.error(f"Error processing budget optimization query: {str(e)}")
            return []
    
    def _extract_product_name(self, query: str) -> str:
        """Extract product name from query."""
        query_lower = query.lower()
        
        # Check for common products
        for product, variations in self.common_products.items():
            for variation in variations:
                if variation in query_lower:
                    return variation
        
        # Extract from context words
        words = query_lower.split()
        for i, word in enumerate(words):
            if word in ["cheapest", "price", "cost", "find", "show", "compare"] and i + 1 < len(words):
                next_word = words[i + 1]
                if next_word not in ["app", "apps", "platform", "platforms", "between", "on"]:
                    return next_word
        
        # Look for product-like words (nouns that aren't platform names)
        platform_words = ['blinkit', 'zepto', 'instamart', 'bigbasket', 'swiggy', 'app', 'apps']
        for word in words:
            if (len(word) > 3 and 
                word not in platform_words and 
                word not in ['cheapest', 'price', 'cost', 'find', 'show', 'compare', 'between', 'discount']):
                return word
        
        return ""
    
    def _extract_platform_name(self, query: str) -> str:
        """Extract platform name from query."""
        query_lower = query.lower()
        
        for platform, variations in self.platform_mappings.items():
            for variation in variations:
                if variation in query_lower:
                    return platform
        
        return ""
    
    def _extract_platforms_for_comparison(self, query: str) -> List[str]:
        """Extract platform names for comparison queries."""
        query_lower = query.lower()
        platforms = []
        
        for platform, variations in self.platform_mappings.items():
            for variation in variations:
                if variation in query_lower:
                    platforms.append(platform)
                    break
        
        return list(set(platforms))  # Remove duplicates
    
    def _extract_discount_percentage(self, query: str) -> float:
        """Extract discount percentage from query."""
        # Look for patterns like "30%", "30 percent", etc.
        percentage_match = re.search(r'(\d+)%', query)
        if percentage_match:
            return float(percentage_match.group(1))
        
        percent_match = re.search(r'(\d+)\s*percent', query)
        if percent_match:
            return float(percent_match.group(1))
        
        # Look for "X percent off" or "X% off"
        off_match = re.search(r'(\d+)(?:%|\s*percent)\s*off', query)
        if off_match:
            return float(off_match.group(1))
        
        return 0.0
    
    def _extract_budget_amount(self, query: str) -> float:
        """Extract budget amount from query."""
        # Look for patterns like "₹1000", "Rs 1000", "1000 rupees"
        rupee_match = re.search(r'₹\s*(\d+(?:,\d+)*)', query)
        if rupee_match:
            amount_str = rupee_match.group(1).replace(',', '')
            return float(amount_str)
        
        rs_match = re.search(r'rs\.?\s*(\d+(?:,\d+)*)', query, re.IGNORECASE)
        if rs_match:
            amount_str = rs_match.group(1).replace(',', '')
            return float(amount_str)
        
        rupees_match = re.search(r'(\d+(?:,\d+)*)\s*rupees?', query, re.IGNORECASE)
        if rupees_match:
            amount_str = rupees_match.group(1).replace(',', '')
            return float(amount_str)
        
        # Look for standalone numbers that might be budget
        number_match = re.search(r'\b(\d{3,5})\b', query)
        if number_match:
            return float(number_match.group(1))
        
        return 0.0
    
    def _get_product_variations(self, product_name: str) -> List[str]:
        """Get variations of a product name for better matching."""
        variations = [product_name]
        
        # Check if it's a known product with predefined variations
        for product, product_variations in self.common_products.items():
            if product_name.lower() in [v.lower() for v in product_variations]:
                variations.extend(product_variations)
                break
        
        # Add common variations
        if product_name.endswith('s'):
            variations.append(product_name[:-1])  # Remove plural
        else:
            variations.append(product_name + 's')  # Add plural
        
        return list(set(variations))
    
    def _get_platform_variations(self, platform_name: str) -> List[str]:
        """Get variations of a platform name for better matching."""
        return self.platform_mappings.get(platform_name.lower(), [platform_name])
    
    def _optimize_grocery_selection(self, items: List, budget: float) -> List:
        """
        Optimize grocery selection within budget using a simple greedy algorithm.
        Prioritizes high-discount items and essential categories.
        """
        # Sort items by value score (discount percentage / price ratio)
        def calculate_value_score(item):
            discount = item.discount_percentage or 0
            price = float(item.price)
            # Higher discount and lower price = higher score
            return (discount + 10) / price  # +10 to avoid division issues
        
        sorted_items = sorted(items, key=calculate_value_score, reverse=True)
        
        selected = []
        total_cost = 0
        category_counts = {}
        
        for item in sorted_items:
            item_price = float(item.price)
            category = getattr(item, 'category_name', 'other')
            
            # Check if adding this item exceeds budget
            if total_cost + item_price > budget:
                continue
            
            # Limit items per category to ensure variety
            if category_counts.get(category, 0) >= 3:
                continue
            
            selected.append(item)
            total_cost += item_price
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Stop if we have enough items or used most of the budget
            if len(selected) >= 20 or total_cost >= budget * 0.9:
                break
        
        return selected


# Singleton instance
_sample_query_handlers = None

def get_sample_query_handlers() -> SampleQueryHandlers:
    """Get singleton instance of SampleQueryHandlers."""
    global _sample_query_handlers
    if _sample_query_handlers is None:
        _sample_query_handlers = SampleQueryHandlers()
    return _sample_query_handlers