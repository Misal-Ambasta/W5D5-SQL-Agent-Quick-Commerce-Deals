"""
Query Result Processing and Pagination for Quick Commerce Deals platform.
Implements statistical sampling, pagination, result formatting, and caching.
"""

import logging
import json
import time
import hashlib
import random
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import math
import statistics
import redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class SamplingMethod(Enum):
    """Statistical sampling methods"""
    RANDOM = "random"
    SYSTEMATIC = "systematic"
    STRATIFIED = "stratified"
    TOP_N = "top_n"
    NONE = "none"


class ResultFormat(Enum):
    """Result formatting options"""
    RAW = "raw"
    STRUCTURED = "structured"
    SUMMARY = "summary"
    COMPARISON = "comparison"
    CHART_DATA = "chart_data"


@dataclass
class PaginationConfig:
    """Configuration for result pagination"""
    page: int = 1
    page_size: int = 20
    max_page_size: int = 100
    total_count: Optional[int] = None
    
    def __post_init__(self):
        # Validate and adjust page size
        if self.page_size > self.max_page_size:
            self.page_size = self.max_page_size
        if self.page_size < 1:
            self.page_size = 1
        if self.page < 1:
            self.page = 1


@dataclass
class SamplingConfig:
    """Configuration for statistical sampling"""
    method: SamplingMethod = SamplingMethod.RANDOM
    sample_size: int = 1000
    confidence_level: float = 0.95
    margin_of_error: float = 0.05
    stratify_by: Optional[str] = None  # Column to stratify by
    
    def calculate_required_sample_size(self, population_size: int) -> int:
        """Calculate required sample size for given population and confidence parameters."""
        if population_size <= self.sample_size:
            return population_size
        
        # Calculate sample size using standard formula
        z_score = 1.96 if self.confidence_level == 0.95 else 2.58  # 95% or 99%
        p = 0.5  # Assume maximum variance
        
        numerator = (z_score ** 2) * p * (1 - p)
        denominator = self.margin_of_error ** 2
        
        sample_size = numerator / denominator
        
        # Adjust for finite population
        if population_size < float('inf'):
            sample_size = sample_size / (1 + (sample_size - 1) / population_size)
        
        return min(int(math.ceil(sample_size)), self.sample_size, population_size)


@dataclass
class CacheConfig:
    """Configuration for result caching"""
    enabled: bool = True
    ttl_seconds: int = 300  # 5 minutes default
    key_prefix: str = "query_result"
    compress: bool = True
    max_size_mb: int = 10  # Maximum cache entry size


@dataclass
class ProcessedResult:
    """Processed query result with metadata"""
    data: List[Dict[str, Any]]
    total_count: int
    sampled: bool
    sampling_method: Optional[SamplingMethod]
    sample_size: Optional[int]
    confidence_level: Optional[float]
    pagination: Optional[Dict[str, Any]]
    format_type: ResultFormat
    processing_time: float
    cached: bool = False
    cache_key: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ResultSummary:
    """Statistical summary of results"""
    total_count: int
    unique_products: int
    unique_platforms: int
    price_range: Tuple[float, float]
    average_price: float
    median_price: float
    discount_stats: Dict[str, float]
    availability_rate: float
    last_updated_range: Tuple[datetime, datetime]


class QueryResultProcessor:
    """
    Processes query results with statistical sampling, pagination, formatting, and caching.
    Optimized for large result sets and frontend consumption.
    """
    
    def __init__(self):
        """Initialize the result processor with Redis cache."""
        self.redis_client = None
        self._initialize_redis()
        
        # Default configurations
        self.default_pagination = PaginationConfig()
        self.default_sampling = SamplingConfig()
        self.default_cache = CacheConfig(ttl_seconds=settings.CACHE_TTL_SECONDS)
        
        # Result formatters
        self.formatters = {
            ResultFormat.RAW: self._format_raw,
            ResultFormat.STRUCTURED: self._format_structured,
            ResultFormat.SUMMARY: self._format_summary,
            ResultFormat.COMPARISON: self._format_comparison,
            ResultFormat.CHART_DATA: self._format_chart_data
        }
    
    def _initialize_redis(self):
        """Initialize Redis connection for caching."""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Redis cache initialization failed: {str(e)}")
            self.redis_client = None
    
    async def process_results(
        self,
        raw_results: List[Dict[str, Any]],
        query: str,
        pagination_config: Optional[PaginationConfig] = None,
        sampling_config: Optional[SamplingConfig] = None,
        cache_config: Optional[CacheConfig] = None,
        result_format: ResultFormat = ResultFormat.STRUCTURED,
        query_context: Optional[Dict[str, Any]] = None
    ) -> ProcessedResult:
        """
        Process raw query results with sampling, pagination, formatting, and caching.
        
        Args:
            raw_results: Raw query results from database
            query: Original query string for cache key generation
            pagination_config: Pagination settings
            sampling_config: Statistical sampling settings
            cache_config: Caching configuration
            result_format: Desired output format
            query_context: Additional context for processing
            
        Returns:
            ProcessedResult with processed data and metadata
        """
        start_time = time.time()
        
        # Use default configs if not provided
        pagination_config = pagination_config or self.default_pagination
        sampling_config = sampling_config or self.default_sampling
        cache_config = cache_config or self.default_cache
        
        logger.info(f"Processing {len(raw_results)} raw results with format: {result_format.value}")
        
        try:
            # Generate cache key
            cache_key = None
            if cache_config.enabled:
                cache_key = self._generate_cache_key(query, pagination_config, sampling_config, result_format)
                
                # Try to get from cache first
                cached_result = await self._get_from_cache(cache_key, cache_config)
                if cached_result:
                    logger.info(f"Returning cached result for key: {cache_key}")
                    return cached_result
            
            # Apply statistical sampling if needed
            sampled_results, sampling_metadata = await self._apply_sampling(
                raw_results, sampling_config
            )
            
            # Apply pagination
            paginated_results, pagination_metadata = await self._apply_pagination(
                sampled_results, pagination_config
            )
            
            # Format results for frontend consumption
            formatted_results = await self._format_results(
                paginated_results, result_format, query_context
            )
            
            # Generate result summary and metadata
            metadata = await self._generate_metadata(
                raw_results, sampled_results, paginated_results, query_context
            )
            metadata.update(sampling_metadata)
            metadata.update(pagination_metadata)
            
            # Create processed result
            processed_result = ProcessedResult(
                data=formatted_results,
                total_count=len(raw_results),
                sampled=sampling_metadata.get('sampled', False),
                sampling_method=sampling_metadata.get('method'),
                sample_size=sampling_metadata.get('sample_size'),
                confidence_level=sampling_metadata.get('confidence_level'),
                pagination=pagination_metadata,
                format_type=result_format,
                processing_time=time.time() - start_time,
                cached=False,
                cache_key=cache_key,
                metadata=metadata
            )
            
            # Cache the result if enabled
            if cache_config.enabled and cache_key:
                await self._cache_result(processed_result, cache_key, cache_config)
            
            logger.info(f"Result processing completed in {processed_result.processing_time:.3f}s")
            return processed_result
            
        except Exception as e:
            logger.error(f"Error processing results: {str(e)}")
            raise
    
    def _generate_cache_key(
        self,
        query: str,
        pagination_config: PaginationConfig,
        sampling_config: SamplingConfig,
        result_format: ResultFormat
    ) -> str:
        """Generate cache key for result caching."""
        key_components = [
            query,
            f"page_{pagination_config.page}",
            f"size_{pagination_config.page_size}",
            f"sample_{sampling_config.method.value}_{sampling_config.sample_size}",
            f"format_{result_format.value}"
        ]
        
        key_string = "|".join(key_components)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{self.default_cache.key_prefix}:{key_hash}"
    
    async def _get_from_cache(
        self, 
        cache_key: str, 
        cache_config: CacheConfig
    ) -> Optional[ProcessedResult]:
        """Retrieve result from cache if available."""
        if not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                result_dict = json.loads(cached_data)
                
                # Reconstruct ProcessedResult
                result = ProcessedResult(**result_dict)
                result.cached = True
                
                return result
                
        except Exception as e:
            logger.warning(f"Error retrieving from cache: {str(e)}")
        
        return None
    
    async def _cache_result(
        self, 
        result: ProcessedResult, 
        cache_key: str, 
        cache_config: CacheConfig
    ) -> bool:
        """Cache the processed result."""
        if not self.redis_client:
            return False
        
        try:
            # Convert to dict for JSON serialization
            result_dict = asdict(result)
            
            # Handle datetime serialization
            result_dict = self._serialize_datetimes(result_dict)
            
            cached_data = json.dumps(result_dict)
            
            # Check size limit
            size_mb = len(cached_data.encode()) / (1024 * 1024)
            if size_mb > cache_config.max_size_mb:
                logger.warning(f"Result too large to cache: {size_mb:.2f}MB > {cache_config.max_size_mb}MB")
                return False
            
            # Cache with TTL
            self.redis_client.setex(cache_key, cache_config.ttl_seconds, cached_data)
            logger.debug(f"Cached result with key: {cache_key}, size: {size_mb:.2f}MB")
            
            return True
            
        except Exception as e:
            logger.warning(f"Error caching result: {str(e)}")
            return False
    
    def _serialize_datetimes(self, obj: Any) -> Any:
        """Recursively serialize datetime objects to ISO strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._serialize_datetimes(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetimes(item) for item in obj]
        else:
            return obj
    
    async def _apply_sampling(
        self, 
        results: List[Dict[str, Any]], 
        sampling_config: SamplingConfig
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Apply statistical sampling to large result sets."""
        
        if len(results) <= sampling_config.sample_size or sampling_config.method == SamplingMethod.NONE:
            return results, {
                'sampled': False,
                'method': None,
                'sample_size': len(results),
                'confidence_level': None
            }
        
        logger.info(f"Applying {sampling_config.method.value} sampling to {len(results)} results")
        
        # Calculate required sample size
        required_sample_size = sampling_config.calculate_required_sample_size(len(results))
        
        sampled_results = []
        
        if sampling_config.method == SamplingMethod.RANDOM:
            sampled_results = random.sample(results, required_sample_size)
        
        elif sampling_config.method == SamplingMethod.SYSTEMATIC:
            # Systematic sampling with regular intervals
            interval = len(results) // required_sample_size
            start = random.randint(0, interval - 1)
            sampled_results = [results[i] for i in range(start, len(results), interval)][:required_sample_size]
        
        elif sampling_config.method == SamplingMethod.STRATIFIED:
            # Stratified sampling by specified column
            if sampling_config.stratify_by:
                sampled_results = await self._stratified_sampling(
                    results, sampling_config.stratify_by, required_sample_size
                )
            else:
                # Fall back to random sampling
                sampled_results = random.sample(results, required_sample_size)
        
        elif sampling_config.method == SamplingMethod.TOP_N:
            # Take top N results (assumes results are already sorted)
            sampled_results = results[:required_sample_size]
        
        metadata = {
            'sampled': True,
            'method': sampling_config.method,
            'sample_size': len(sampled_results),
            'original_size': len(results),
            'confidence_level': sampling_config.confidence_level,
            'margin_of_error': sampling_config.margin_of_error
        }
        
        logger.info(f"Sampling completed: {len(sampled_results)} samples from {len(results)} results")
        return sampled_results, metadata
    
    async def _stratified_sampling(
        self, 
        results: List[Dict[str, Any]], 
        stratify_column: str, 
        sample_size: int
    ) -> List[Dict[str, Any]]:
        """Perform stratified sampling based on a column value."""
        
        # Group results by stratification column
        strata = {}
        for result in results:
            stratum_value = result.get(stratify_column, 'unknown')
            if stratum_value not in strata:
                strata[stratum_value] = []
            strata[stratum_value].append(result)
        
        # Calculate sample size for each stratum (proportional allocation)
        sampled_results = []
        total_population = len(results)
        
        for stratum_value, stratum_results in strata.items():
            stratum_size = len(stratum_results)
            stratum_sample_size = max(1, int((stratum_size / total_population) * sample_size))
            
            if stratum_sample_size >= stratum_size:
                sampled_results.extend(stratum_results)
            else:
                sampled_results.extend(random.sample(stratum_results, stratum_sample_size))
        
        # If we have too many samples, randomly reduce
        if len(sampled_results) > sample_size:
            sampled_results = random.sample(sampled_results, sample_size)
        
        return sampled_results
    
    async def _apply_pagination(
        self, 
        results: List[Dict[str, Any]], 
        pagination_config: PaginationConfig
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Apply pagination to results."""
        
        total_count = len(results)
        pagination_config.total_count = total_count
        
        # Calculate pagination parameters
        total_pages = math.ceil(total_count / pagination_config.page_size)
        start_index = (pagination_config.page - 1) * pagination_config.page_size
        end_index = start_index + pagination_config.page_size
        
        # Extract page results
        paginated_results = results[start_index:end_index]
        
        # Create pagination metadata
        pagination_metadata = {
            'page': pagination_config.page,
            'page_size': pagination_config.page_size,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': pagination_config.page < total_pages,
            'has_previous': pagination_config.page > 1,
            'start_index': start_index + 1,  # 1-based for display
            'end_index': min(end_index, total_count)
        }
        
        logger.debug(f"Pagination applied: page {pagination_config.page}/{total_pages}, "
                    f"showing {len(paginated_results)} of {total_count} results")
        
        return paginated_results, pagination_metadata
    
    async def _format_results(
        self, 
        results: List[Dict[str, Any]], 
        result_format: ResultFormat,
        query_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Format results for frontend consumption."""
        
        formatter = self.formatters.get(result_format, self._format_structured)
        return await formatter(results, query_context)
    
    async def _format_raw(
        self, 
        results: List[Dict[str, Any]], 
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Return raw results without formatting."""
        return results
    
    async def _format_structured(
        self, 
        results: List[Dict[str, Any]], 
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Format results with consistent structure for frontend."""
        formatted_results = []
        
        for result in results:
            formatted_result = {
                'id': result.get('product_id', result.get('id', 0)),
                'product_name': result.get('product_name', result.get('name', '')),
                'platform_name': result.get('platform_name', ''),
                'current_price': float(result.get('current_price', result.get('price', 0))),
                'original_price': float(result.get('original_price', 0)) if result.get('original_price') else None,
                'discount_percentage': float(result.get('discount_percentage', 0)) if result.get('discount_percentage') else None,
                'is_available': bool(result.get('is_available', True)),
                'last_updated': None,  # Will be set below
                'savings': None
            }
            
            # Calculate savings if original price available
            if formatted_result['original_price'] and formatted_result['original_price'] > formatted_result['current_price']:
                formatted_result['savings'] = formatted_result['original_price'] - formatted_result['current_price']
            
            # Handle datetime formatting
            if result.get('last_updated'):
                if isinstance(result['last_updated'], str):
                    formatted_result['last_updated'] = result['last_updated']
                elif hasattr(result['last_updated'], 'isoformat'):
                    formatted_result['last_updated'] = result['last_updated'].isoformat()
                else:
                    formatted_result['last_updated'] = str(result['last_updated'])
            else:
                formatted_result['last_updated'] = datetime.utcnow().isoformat()
            
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    async def _format_summary(
        self, 
        results: List[Dict[str, Any]], 
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Format results as summary statistics."""
        if not results:
            return [{'summary': 'No results found'}]
        
        # Calculate summary statistics
        prices = [float(r.get('current_price', r.get('price', 0))) for r in results if r.get('current_price') or r.get('price')]
        platforms = list(set(r.get('platform_name', '') for r in results if r.get('platform_name')))
        products = list(set(r.get('product_name', r.get('name', '')) for r in results if r.get('product_name') or r.get('name')))
        
        summary = {
            'total_results': len(results),
            'unique_products': len(products),
            'unique_platforms': len(platforms),
            'price_statistics': {
                'min_price': min(prices) if prices else 0,
                'max_price': max(prices) if prices else 0,
                'average_price': statistics.mean(prices) if prices else 0,
                'median_price': statistics.median(prices) if prices else 0
            },
            'platforms': platforms,
            'sample_products': products[:10]  # Show first 10 products
        }
        
        return [summary]
    
    async def _format_comparison(
        self, 
        results: List[Dict[str, Any]], 
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Format results for price comparison display."""
        if not results:
            return []
        
        # Group by product for comparison
        product_groups = {}
        for result in results:
            product_name = result.get('product_name', result.get('name', 'Unknown'))
            if product_name not in product_groups:
                product_groups[product_name] = []
            product_groups[product_name].append(result)
        
        comparison_results = []
        for product_name, product_results in product_groups.items():
            # Sort by price for each product
            sorted_results = sorted(product_results, key=lambda x: float(x.get('current_price', x.get('price', 0))))
            
            comparison = {
                'product_name': product_name,
                'platforms': [],
                'cheapest_platform': None,
                'most_expensive_platform': None,
                'price_range': None,
                'average_price': None
            }
            
            prices = []
            for result in sorted_results:
                price = float(result.get('current_price', result.get('price', 0)))
                prices.append(price)
                
                platform_info = {
                    'platform_name': result.get('platform_name', ''),
                    'price': price,
                    'original_price': float(result.get('original_price', 0)) if result.get('original_price') else None,
                    'discount_percentage': float(result.get('discount_percentage', 0)) if result.get('discount_percentage') else None,
                    'is_available': bool(result.get('is_available', True))
                }
                comparison['platforms'].append(platform_info)
            
            if prices:
                comparison['cheapest_platform'] = sorted_results[0].get('platform_name', '')
                comparison['most_expensive_platform'] = sorted_results[-1].get('platform_name', '')
                comparison['price_range'] = {'min': min(prices), 'max': max(prices)}
                comparison['average_price'] = statistics.mean(prices)
            
            comparison_results.append(comparison)
        
        return comparison_results
    
    async def _format_chart_data(
        self, 
        results: List[Dict[str, Any]], 
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Format results for chart/visualization consumption."""
        if not results:
            return []
        
        # Create data suitable for charts
        chart_data = {
            'price_distribution': [],
            'platform_comparison': [],
            'discount_analysis': [],
            'availability_stats': []
        }
        
        # Price distribution data
        prices = [float(r.get('current_price', r.get('price', 0))) for r in results if r.get('current_price') or r.get('price')]
        if prices:
            # Create price buckets
            min_price, max_price = min(prices), max(prices)
            bucket_size = (max_price - min_price) / 10 if max_price > min_price else 1
            
            buckets = {}
            for price in prices:
                bucket = int((price - min_price) / bucket_size)
                bucket_key = f"₹{min_price + bucket * bucket_size:.0f}-₹{min_price + (bucket + 1) * bucket_size:.0f}"
                buckets[bucket_key] = buckets.get(bucket_key, 0) + 1
            
            chart_data['price_distribution'] = [{'range': k, 'count': v} for k, v in buckets.items()]
        
        # Platform comparison data
        platform_stats = {}
        for result in results:
            platform = result.get('platform_name', 'Unknown')
            price = float(result.get('current_price', result.get('price', 0)))
            
            if platform not in platform_stats:
                platform_stats[platform] = {'prices': [], 'count': 0}
            
            platform_stats[platform]['prices'].append(price)
            platform_stats[platform]['count'] += 1
        
        for platform, stats in platform_stats.items():
            if stats['prices']:
                chart_data['platform_comparison'].append({
                    'platform': platform,
                    'average_price': statistics.mean(stats['prices']),
                    'min_price': min(stats['prices']),
                    'max_price': max(stats['prices']),
                    'product_count': stats['count']
                })
        
        return [chart_data]
    
    async def _generate_metadata(
        self,
        raw_results: List[Dict[str, Any]],
        sampled_results: List[Dict[str, Any]],
        paginated_results: List[Dict[str, Any]],
        query_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive metadata about the results."""
        
        metadata = {
            'result_counts': {
                'raw': len(raw_results),
                'sampled': len(sampled_results),
                'paginated': len(paginated_results)
            },
            'processing_timestamp': datetime.utcnow().isoformat(),
            'data_freshness': await self._calculate_data_freshness(raw_results),
            'quality_metrics': await self._calculate_quality_metrics(raw_results)
        }
        
        # Add query context if provided
        if query_context:
            metadata['query_context'] = query_context
        
        return metadata
    
    async def _calculate_data_freshness(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate data freshness metrics."""
        if not results:
            return {'status': 'no_data'}
        
        # Extract last_updated timestamps
        timestamps = []
        for result in results:
            last_updated = result.get('last_updated')
            if last_updated:
                if isinstance(last_updated, str):
                    try:
                        last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    except:
                        continue
                if isinstance(last_updated, datetime):
                    timestamps.append(last_updated)
        
        if not timestamps:
            return {'status': 'no_timestamps'}
        
        now = datetime.utcnow()
        # Ensure all timestamps are timezone-naive for comparison
        naive_timestamps = []
        for ts in timestamps:
            if ts.tzinfo is not None:
                # Convert to UTC and make naive
                utc_tuple = ts.utctimetuple()
                naive_ts = datetime(*utc_tuple[:6])
                naive_timestamps.append(naive_ts)
            else:
                naive_timestamps.append(ts)
        
        ages = [(now - ts).total_seconds() / 3600 for ts in naive_timestamps]  # Age in hours
        
        return {
            'status': 'calculated',
            'oldest_data_hours': max(ages),
            'newest_data_hours': min(ages),
            'average_age_hours': statistics.mean(ages),
            'stale_data_count': len([age for age in ages if age > 24])  # Data older than 24 hours
        }
    
    async def _calculate_quality_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate data quality metrics."""
        if not results:
            return {'status': 'no_data'}
        
        total_results = len(results)
        
        # Count missing values for key fields
        missing_counts = {
            'product_name': sum(1 for r in results if not r.get('product_name') and not r.get('name')),
            'platform_name': sum(1 for r in results if not r.get('platform_name')),
            'price': sum(1 for r in results if not r.get('current_price') and not r.get('price')),
            'availability': sum(1 for r in results if r.get('is_available') is None)
        }
        
        # Calculate completeness percentages
        completeness = {
            field: ((total_results - missing) / total_results) * 100
            for field, missing in missing_counts.items()
        }
        
        # Count available vs unavailable products
        available_count = sum(1 for r in results if r.get('is_available', True))
        availability_rate = (available_count / total_results) * 100
        
        return {
            'status': 'calculated',
            'completeness_percentages': completeness,
            'availability_rate': availability_rate,
            'total_records': total_results,
            'missing_value_counts': missing_counts
        }
    
    async def invalidate_cache(self, pattern: str = None) -> int:
        """
        Invalidate cached results matching a pattern.
        
        Args:
            pattern: Redis key pattern to match (default: all query results)
            
        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0
        
        try:
            pattern = pattern or f"{self.default_cache.key_prefix}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted_count} cached results")
                return deleted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {str(e)}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics and health information."""
        if not self.redis_client:
            return {'status': 'disabled', 'error': 'Redis not available'}
        
        try:
            info = self.redis_client.info()
            
            # Get query result cache keys
            pattern = f"{self.default_cache.key_prefix}:*"
            cache_keys = self.redis_client.keys(pattern)
            
            return {
                'status': 'active',
                'redis_info': {
                    'used_memory_human': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                    'total_commands_processed': info.get('total_commands_processed')
                },
                'cache_stats': {
                    'total_query_cache_keys': len(cache_keys),
                    'cache_key_prefix': self.default_cache.key_prefix,
                    'default_ttl_seconds': self.default_cache.ttl_seconds
                }
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}


# Singleton instance for global use
_result_processor_instance = None

def get_result_processor() -> QueryResultProcessor:
    """Get singleton instance of QueryResultProcessor."""
    global _result_processor_instance
    if _result_processor_instance is None:
        _result_processor_instance = QueryResultProcessor()
    return _result_processor_instance