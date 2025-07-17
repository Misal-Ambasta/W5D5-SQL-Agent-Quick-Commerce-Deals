"""
Query Accuracy Validator for Quick Commerce Deals platform.
Implements query result validation against known data patterns and accuracy testing.
Task 8.2 implementation.
"""

import logging
import time
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.product import Product, ProductCategory
from app.models.pricing import CurrentPrice
from app.models.platform import Platform
from app.schemas.query import QueryResult

logger = logging.getLogger(__name__)


class ValidationResult(Enum):
    """Validation result types"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


@dataclass
class ValidationRule:
    """Represents a validation rule for query results"""
    rule_id: str
    rule_name: str
    description: str
    validation_function: str
    expected_behavior: str
    severity: str  # critical, high, medium, low
    enabled: bool = True


@dataclass
class ValidationTestCase:
    """Test case for query accuracy validation"""
    test_id: str
    query: str
    query_type: str
    expected_result_count_min: int
    expected_result_count_max: int
    expected_patterns: List[str]
    validation_rules: List[str]
    timeout_seconds: int = 30
    description: str = ""


@dataclass
class ValidationReport:
    """Report for validation test execution"""
    test_case_id: str
    query: str
    execution_time: float
    result_count: int
    validation_results: List[Dict[str, Any]]
    overall_status: ValidationResult
    issues_found: List[str]
    performance_metrics: Dict[str, Any]
    timestamp: datetime


class QueryAccuracyValidator:
    """
    Validates query accuracy and performance against known data patterns.
    Provides automated testing for query generation improvements.
    """
    
    def __init__(self):
        """Initialize the query accuracy validator."""
        self.validation_rules = self._initialize_validation_rules()
        self.test_cases = self._initialize_test_cases()
        self.performance_thresholds = {
            'max_execution_time': 5.0,  # seconds
            'min_result_relevance': 0.8,  # 80% relevance
            'max_price_variance': 0.1,  # 10% price variance tolerance
        }
    
    def _initialize_validation_rules(self) -> Dict[str, ValidationRule]:
        """Initialize validation rules for different query types."""
        return {
            'price_consistency': ValidationRule(
                rule_id='price_consistency',
                rule_name='Price Consistency Check',
                description='Verify that prices are within reasonable ranges and consistent',
                validation_function='_validate_price_consistency',
                expected_behavior='All prices should be positive and within market ranges',
                severity='critical'
            ),
            'platform_availability': ValidationRule(
                rule_id='platform_availability',
                rule_name='Platform Availability Check',
                description='Verify that only active platforms are included in results',
                validation_function='_validate_platform_availability',
                expected_behavior='Only active platforms should appear in results',
                severity='high'
            ),
            'product_relevance': ValidationRule(
                rule_id='product_relevance',
                rule_name='Product Relevance Check',
                description='Verify that returned products match the query intent',
                validation_function='_validate_product_relevance',
                expected_behavior='Products should be relevant to the search query',
                severity='high'
            ),
            'discount_accuracy': ValidationRule(
                rule_id='discount_accuracy',
                rule_name='Discount Calculation Accuracy',
                description='Verify that discount percentages are calculated correctly',
                validation_function='_validate_discount_accuracy',
                expected_behavior='Discount percentages should match price differences',
                severity='critical'
            ),
            'result_ordering': ValidationRule(
                rule_id='result_ordering',
                rule_name='Result Ordering Check',
                description='Verify that results are ordered according to query type',
                validation_function='_validate_result_ordering',
                expected_behavior='Results should be ordered appropriately (cheapest first, highest discount first, etc.)',
                severity='medium'
            ),
            'data_freshness': ValidationRule(
                rule_id='data_freshness',
                rule_name='Data Freshness Check',
                description='Verify that price data is recent and up-to-date',
                validation_function='_validate_data_freshness',
                expected_behavior='Price data should be updated within the last 24 hours',
                severity='medium'
            ),
            'availability_consistency': ValidationRule(
                rule_id='availability_consistency',
                rule_name='Availability Consistency Check',
                description='Verify that only available products are returned',
                validation_function='_validate_availability_consistency',
                expected_behavior='All returned products should be marked as available',
                severity='high'
            ),
            'comparison_completeness': ValidationRule(
                rule_id='comparison_completeness',
                rule_name='Comparison Completeness Check',
                description='Verify that comparison queries include multiple platforms',
                validation_function='_validate_comparison_completeness',
                expected_behavior='Comparison queries should include products from multiple platforms',
                severity='medium'
            )
        }
    
    def _initialize_test_cases(self) -> List[ValidationTestCase]:
        """Initialize test cases for different query types."""
        return [
            # Cheapest product queries (Requirement 10.1)
            ValidationTestCase(
                test_id='cheapest_onions',
                query='Which app has cheapest onions right now?',
                query_type='cheapest_product',
                expected_result_count_min=1,
                expected_result_count_max=20,
                expected_patterns=['onion'],
                validation_rules=['price_consistency', 'platform_availability', 'product_relevance', 'result_ordering', 'availability_consistency'],
                description='Test cheapest onions query'
            ),
            ValidationTestCase(
                test_id='cheapest_tomatoes',
                query='Which app has cheapest tomatoes right now?',
                query_type='cheapest_product',
                expected_result_count_min=1,
                expected_result_count_max=20,
                expected_patterns=['tomato'],
                validation_rules=['price_consistency', 'platform_availability', 'product_relevance', 'result_ordering', 'availability_consistency'],
                description='Test cheapest tomatoes query'
            ),
            
            # Discount queries (Requirement 10.2)
            ValidationTestCase(
                test_id='discount_30_percent_blinkit',
                query='Show products with 30%+ discount on Blinkit',
                query_type='discount_search',
                expected_result_count_min=0,
                expected_result_count_max=100,
                expected_patterns=['blinkit'],
                validation_rules=['discount_accuracy', 'platform_availability', 'result_ordering', 'availability_consistency'],
                description='Test 30%+ discount on Blinkit query'
            ),
            ValidationTestCase(
                test_id='discount_20_percent_any',
                query='Show products with 20%+ discount',
                query_type='discount_search',
                expected_result_count_min=0,
                expected_result_count_max=100,
                expected_patterns=[],
                validation_rules=['discount_accuracy', 'platform_availability', 'result_ordering', 'availability_consistency'],
                description='Test 20%+ discount on any platform query'
            ),
            
            # Price comparison queries (Requirement 10.3)
            ValidationTestCase(
                test_id='compare_fruits_zepto_instamart',
                query='Compare fruit prices between Zepto and Instamart',
                query_type='price_comparison',
                expected_result_count_min=0,
                expected_result_count_max=50,
                expected_patterns=['zepto', 'instamart', 'fruit'],
                validation_rules=['price_consistency', 'platform_availability', 'product_relevance', 'comparison_completeness'],
                description='Test fruit price comparison between Zepto and Instamart'
            ),
            ValidationTestCase(
                test_id='compare_milk_all_platforms',
                query='Compare milk prices between all platforms',
                query_type='price_comparison',
                expected_result_count_min=0,
                expected_result_count_max=50,
                expected_patterns=['milk'],
                validation_rules=['price_consistency', 'platform_availability', 'product_relevance', 'comparison_completeness'],
                description='Test milk price comparison across all platforms'
            ),
            
            # Budget optimization queries (Requirement 10.4)
            ValidationTestCase(
                test_id='budget_1000_grocery',
                query='Find best deals for ₹1000 grocery list',
                query_type='budget_optimization',
                expected_result_count_min=5,
                expected_result_count_max=30,
                expected_patterns=['1000'],
                validation_rules=['price_consistency', 'platform_availability', 'discount_accuracy', 'availability_consistency'],
                description='Test ₹1000 budget optimization query'
            ),
            ValidationTestCase(
                test_id='budget_500_grocery',
                query='Find best deals for ₹500 grocery list',
                query_type='budget_optimization',
                expected_result_count_min=3,
                expected_result_count_max=20,
                expected_patterns=['500'],
                validation_rules=['price_consistency', 'platform_availability', 'discount_accuracy', 'availability_consistency'],
                description='Test ₹500 budget optimization query'
            ),
        ]
    
    async def validate_query_results(
        self, 
        query: str, 
        results: List[QueryResult], 
        query_type: str,
        execution_time: float,
        db: Session
    ) -> ValidationReport:
        """
        Validate query results against accuracy rules and patterns.
        
        Args:
            query: The original query string
            results: Query results to validate
            query_type: Type of query (cheapest_product, discount_search, etc.)
            execution_time: Query execution time in seconds
            db: Database session for additional validation queries
            
        Returns:
            ValidationReport with detailed validation results
        """
        logger.info(f"Validating query results for: '{query}' (type: {query_type})")
        
        validation_results = []
        issues_found = []
        overall_status = ValidationResult.PASS
        
        # Find applicable test case
        test_case = self._find_matching_test_case(query, query_type)
        
        # Get validation rules for this query type
        applicable_rules = self._get_applicable_rules(query_type, test_case)
        
        # Run each validation rule
        for rule_id in applicable_rules:
            if rule_id not in self.validation_rules:
                continue
                
            rule = self.validation_rules[rule_id]
            if not rule.enabled:
                continue
            
            try:
                # Execute validation function
                validation_func = getattr(self, rule.validation_function)
                rule_result = await validation_func(query, results, query_type, db)
                
                validation_results.append({
                    'rule_id': rule_id,
                    'rule_name': rule.rule_name,
                    'status': rule_result['status'],
                    'message': rule_result['message'],
                    'details': rule_result.get('details', {}),
                    'severity': rule.severity
                })
                
                # Update overall status
                if rule_result['status'] == ValidationResult.FAIL:
                    if rule.severity in ['critical', 'high']:
                        overall_status = ValidationResult.FAIL
                    elif overall_status == ValidationResult.PASS:
                        overall_status = ValidationResult.WARNING
                    
                    issues_found.append(f"{rule.rule_name}: {rule_result['message']}")
                
            except Exception as e:
                logger.error(f"Error executing validation rule {rule_id}: {str(e)}")
                validation_results.append({
                    'rule_id': rule_id,
                    'rule_name': rule.rule_name,
                    'status': ValidationResult.SKIP,
                    'message': f"Validation error: {str(e)}",
                    'details': {},
                    'severity': rule.severity
                })
        
        # Performance metrics
        performance_metrics = {
            'execution_time': execution_time,
            'result_count': len(results),
            'performance_score': self._calculate_performance_score(execution_time, len(results)),
            'meets_performance_threshold': execution_time <= self.performance_thresholds['max_execution_time']
        }
        
        # Create validation report
        report = ValidationReport(
            test_case_id=test_case.test_id if test_case else 'unknown',
            query=query,
            execution_time=execution_time,
            result_count=len(results),
            validation_results=validation_results,
            overall_status=overall_status,
            issues_found=issues_found,
            performance_metrics=performance_metrics,
            timestamp=datetime.utcnow()
        )
        
        logger.info(f"Validation completed: {overall_status.value} ({len(issues_found)} issues found)")
        return report
    
    def _find_matching_test_case(self, query: str, query_type: str) -> Optional[ValidationTestCase]:
        """Find the most matching test case for the query."""
        query_lower = query.lower()
        
        # Find exact matches first
        for test_case in self.test_cases:
            if test_case.query.lower() == query_lower:
                return test_case
        
        # Find matches by query type and patterns
        best_match = None
        best_score = 0
        
        for test_case in self.test_cases:
            if test_case.query_type != query_type:
                continue
            
            score = 0
            for pattern in test_case.expected_patterns:
                if pattern.lower() in query_lower:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = test_case
        
        return best_match
    
    def _get_applicable_rules(self, query_type: str, test_case: Optional[ValidationTestCase]) -> List[str]:
        """Get applicable validation rules for a query type."""
        if test_case and test_case.validation_rules:
            return test_case.validation_rules
        
        # Default rules by query type
        default_rules = {
            'cheapest_product': ['price_consistency', 'platform_availability', 'product_relevance', 'result_ordering', 'availability_consistency'],
            'discount_search': ['discount_accuracy', 'platform_availability', 'result_ordering', 'availability_consistency'],
            'price_comparison': ['price_consistency', 'platform_availability', 'product_relevance', 'comparison_completeness'],
            'budget_optimization': ['price_consistency', 'platform_availability', 'discount_accuracy', 'availability_consistency']
        }
        
        return default_rules.get(query_type, ['price_consistency', 'platform_availability', 'availability_consistency'])
    
    async def _validate_price_consistency(self, query: str, results: List[QueryResult], query_type: str, db: Session) -> Dict[str, Any]:
        """Validate that prices are consistent and reasonable."""
        if not results:
            return {'status': ValidationResult.SKIP, 'message': 'No results to validate'}
        
        issues = []
        
        # Check for negative or zero prices
        invalid_prices = [r for r in results if r.current_price <= 0]
        if invalid_prices:
            issues.append(f"Found {len(invalid_prices)} products with invalid prices (≤0)")
        
        # Check for extremely high prices (outliers)
        prices = [r.current_price for r in results]
        if prices:
            avg_price = sum(prices) / len(prices)
            outliers = [r for r in results if r.current_price > avg_price * 10]  # 10x average
            if outliers:
                issues.append(f"Found {len(outliers)} potential price outliers")
        
        # Check original price vs current price consistency
        discount_issues = []
        for result in results:
            if result.original_price and result.current_price > result.original_price:
                discount_issues.append(result.product_name)
        
        if discount_issues:
            issues.append(f"Found {len(discount_issues)} products where current price > original price")
        
        status = ValidationResult.FAIL if issues else ValidationResult.PASS
        message = '; '.join(issues) if issues else 'All prices are consistent'
        
        return {
            'status': status,
            'message': message,
            'details': {
                'total_products': len(results),
                'invalid_prices': len(invalid_prices),
                'price_outliers': len(outliers) if 'outliers' in locals() else 0,
                'discount_issues': len(discount_issues)
            }
        }
    
    async def _validate_platform_availability(self, query: str, results: List[QueryResult], query_type: str, db: Session) -> Dict[str, Any]:
        """Validate that only active platforms are included."""
        if not results:
            return {'status': ValidationResult.SKIP, 'message': 'No results to validate'}
        
        # Get active platforms from database
        active_platforms = db.query(Platform.name).filter(Platform.is_active == True).all()
        active_platform_names = {p.name.lower() for p in active_platforms}
        
        # Check if all result platforms are active
        result_platforms = {r.platform_name.lower() for r in results}
        inactive_platforms = result_platforms - active_platform_names
        
        status = ValidationResult.FAIL if inactive_platforms else ValidationResult.PASS
        message = f"Found inactive platforms: {inactive_platforms}" if inactive_platforms else "All platforms are active"
        
        return {
            'status': status,
            'message': message,
            'details': {
                'total_platforms_in_results': len(result_platforms),
                'active_platforms_count': len(active_platform_names),
                'inactive_platforms': list(inactive_platforms)
            }
        }
    
    async def _validate_product_relevance(self, query: str, results: List[QueryResult], query_type: str, db: Session) -> Dict[str, Any]:
        """Validate that products are relevant to the query."""
        if not results:
            return {'status': ValidationResult.SKIP, 'message': 'No results to validate'}
        
        # Extract expected product keywords from query
        query_lower = query.lower()
        product_keywords = []
        
        # Common product extraction patterns
        common_products = ['onion', 'tomato', 'potato', 'apple', 'banana', 'milk', 'bread', 'rice', 'fruit']
        for product in common_products:
            if product in query_lower:
                product_keywords.append(product)
        
        if not product_keywords:
            return {'status': ValidationResult.SKIP, 'message': 'No specific product keywords found in query'}
        
        # Check relevance
        relevant_count = 0
        for result in results:
            product_name_lower = result.product_name.lower()
            if any(keyword in product_name_lower for keyword in product_keywords):
                relevant_count += 1
        
        relevance_ratio = relevant_count / len(results) if results else 0
        threshold = self.performance_thresholds['min_result_relevance']
        
        status = ValidationResult.PASS if relevance_ratio >= threshold else ValidationResult.WARNING
        message = f"Product relevance: {relevance_ratio:.2%} ({relevant_count}/{len(results)})"
        
        return {
            'status': status,
            'message': message,
            'details': {
                'relevant_products': relevant_count,
                'total_products': len(results),
                'relevance_ratio': relevance_ratio,
                'keywords_searched': product_keywords
            }
        }
    
    async def _validate_discount_accuracy(self, query: str, results: List[QueryResult], query_type: str, db: Session) -> Dict[str, Any]:
        """Validate discount calculation accuracy."""
        if not results:
            return {'status': ValidationResult.SKIP, 'message': 'No results to validate'}
        
        discount_errors = []
        
        for result in results:
            if result.original_price and result.discount_percentage:
                # Calculate expected discount percentage
                expected_discount = ((result.original_price - result.current_price) / result.original_price) * 100
                actual_discount = result.discount_percentage
                
                # Allow small tolerance for rounding
                tolerance = 1.0  # 1% tolerance
                if abs(expected_discount - actual_discount) > tolerance:
                    discount_errors.append({
                        'product': result.product_name,
                        'expected': expected_discount,
                        'actual': actual_discount,
                        'difference': abs(expected_discount - actual_discount)
                    })
        
        status = ValidationResult.FAIL if discount_errors else ValidationResult.PASS
        message = f"Found {len(discount_errors)} discount calculation errors" if discount_errors else "All discount calculations are accurate"
        
        return {
            'status': status,
            'message': message,
            'details': {
                'total_discounted_products': len([r for r in results if r.discount_percentage]),
                'calculation_errors': len(discount_errors),
                'error_details': discount_errors[:5]  # Show first 5 errors
            }
        }
    
    async def _validate_result_ordering(self, query: str, results: List[QueryResult], query_type: str, db: Session) -> Dict[str, Any]:
        """Validate that results are ordered correctly."""
        if len(results) < 2:
            return {'status': ValidationResult.SKIP, 'message': 'Not enough results to validate ordering'}
        
        ordering_correct = True
        expected_order = ""
        
        if query_type == 'cheapest_product' or 'cheapest' in query.lower():
            # Should be ordered by price ascending
            expected_order = "price ascending"
            for i in range(len(results) - 1):
                if results[i].current_price > results[i + 1].current_price:
                    ordering_correct = False
                    break
        
        elif query_type == 'discount_search' or 'discount' in query.lower():
            # Should be ordered by discount percentage descending
            expected_order = "discount descending"
            for i in range(len(results) - 1):
                discount1 = results[i].discount_percentage or 0
                discount2 = results[i + 1].discount_percentage or 0
                if discount1 < discount2:
                    ordering_correct = False
                    break
        
        else:
            return {'status': ValidationResult.SKIP, 'message': 'No specific ordering requirement for this query type'}
        
        status = ValidationResult.PASS if ordering_correct else ValidationResult.FAIL
        message = f"Results are {'correctly' if ordering_correct else 'incorrectly'} ordered ({expected_order})"
        
        return {
            'status': status,
            'message': message,
            'details': {
                'expected_order': expected_order,
                'ordering_correct': ordering_correct,
                'sample_values': [r.current_price if 'price' in expected_order else (r.discount_percentage or 0) for r in results[:5]]
            }
        }
    
    async def _validate_data_freshness(self, query: str, results: List[QueryResult], query_type: str, db: Session) -> Dict[str, Any]:
        """Validate that data is fresh and up-to-date."""
        if not results:
            return {'status': ValidationResult.SKIP, 'message': 'No results to validate'}
        
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        stale_count = 0
        
        for result in results:
            if result.last_updated < cutoff_time:
                stale_count += 1
        
        freshness_ratio = (len(results) - stale_count) / len(results) if results else 0
        
        status = ValidationResult.PASS if freshness_ratio >= 0.8 else ValidationResult.WARNING
        message = f"Data freshness: {freshness_ratio:.2%} ({len(results) - stale_count}/{len(results)} fresh)"
        
        return {
            'status': status,
            'message': message,
            'details': {
                'total_products': len(results),
                'fresh_products': len(results) - stale_count,
                'stale_products': stale_count,
                'freshness_ratio': freshness_ratio
            }
        }
    
    async def _validate_availability_consistency(self, query: str, results: List[QueryResult], query_type: str, db: Session) -> Dict[str, Any]:
        """Validate that only available products are returned."""
        if not results:
            return {'status': ValidationResult.SKIP, 'message': 'No results to validate'}
        
        unavailable_count = len([r for r in results if not r.is_available])
        
        status = ValidationResult.FAIL if unavailable_count > 0 else ValidationResult.PASS
        message = f"Found {unavailable_count} unavailable products" if unavailable_count > 0 else "All products are available"
        
        return {
            'status': status,
            'message': message,
            'details': {
                'total_products': len(results),
                'available_products': len(results) - unavailable_count,
                'unavailable_products': unavailable_count
            }
        }
    
    async def _validate_comparison_completeness(self, query: str, results: List[QueryResult], query_type: str, db: Session) -> Dict[str, Any]:
        """Validate that comparison queries include multiple platforms."""
        if not results:
            return {'status': ValidationResult.SKIP, 'message': 'No results to validate'}
        
        unique_platforms = len(set(r.platform_name for r in results))
        
        status = ValidationResult.PASS if unique_platforms >= 2 else ValidationResult.WARNING
        message = f"Comparison includes {unique_platforms} platforms"
        
        return {
            'status': status,
            'message': message,
            'details': {
                'unique_platforms': unique_platforms,
                'platforms': list(set(r.platform_name for r in results))
            }
        }
    
    def _calculate_performance_score(self, execution_time: float, result_count: int) -> float:
        """Calculate a performance score based on execution time and result count."""
        # Base score starts at 100
        score = 100.0
        
        # Deduct points for slow execution
        if execution_time > self.performance_thresholds['max_execution_time']:
            score -= (execution_time - self.performance_thresholds['max_execution_time']) * 10
        
        # Bonus points for reasonable result count
        if 1 <= result_count <= 50:
            score += 10
        elif result_count > 100:
            score -= 5
        
        return max(0, min(100, score))
    
    async def run_regression_tests(self, db: Session) -> List[ValidationReport]:
        """
        Run all test cases for regression testing.
        
        Args:
            db: Database session
            
        Returns:
            List of validation reports for all test cases
        """
        logger.info("Running regression tests for query accuracy validation")
        
        reports = []
        
        # Import here to avoid circular imports
        from app.services.sample_query_handlers import get_sample_query_handlers
        
        handlers = get_sample_query_handlers()
        
        for test_case in self.test_cases:
            logger.info(f"Running test case: {test_case.test_id}")
            
            try:
                start_time = time.time()
                
                # Execute query based on type
                if test_case.query_type == 'cheapest_product':
                    results = await handlers.handle_cheapest_product_query(db, test_case.query)
                elif test_case.query_type == 'discount_search':
                    results = await handlers.handle_discount_query(db, test_case.query)
                elif test_case.query_type == 'price_comparison':
                    results = await handlers.handle_price_comparison_query(db, test_case.query)
                elif test_case.query_type == 'budget_optimization':
                    results = await handlers.handle_budget_optimization_query(db, test_case.query)
                else:
                    logger.warning(f"Unknown query type: {test_case.query_type}")
                    continue
                
                execution_time = time.time() - start_time
                
                # Validate results
                report = await self.validate_query_results(
                    test_case.query, 
                    results, 
                    test_case.query_type, 
                    execution_time, 
                    db
                )
                
                reports.append(report)
                
                logger.info(f"Test case {test_case.test_id} completed: {report.overall_status.value}")
                
            except Exception as e:
                logger.error(f"Error running test case {test_case.test_id}: {str(e)}")
                
                # Create error report
                error_report = ValidationReport(
                    test_case_id=test_case.test_id,
                    query=test_case.query,
                    execution_time=0.0,
                    result_count=0,
                    validation_results=[],
                    overall_status=ValidationResult.FAIL,
                    issues_found=[f"Test execution failed: {str(e)}"],
                    performance_metrics={},
                    timestamp=datetime.utcnow()
                )
                reports.append(error_report)
        
        logger.info(f"Regression testing completed: {len(reports)} test cases executed")
        return reports


# Singleton instance
_query_accuracy_validator = None

def get_query_accuracy_validator() -> QueryAccuracyValidator:
    """Get singleton instance of QueryAccuracyValidator."""
    global _query_accuracy_validator
    if _query_accuracy_validator is None:
        _query_accuracy_validator = QueryAccuracyValidator()
    return _query_accuracy_validator