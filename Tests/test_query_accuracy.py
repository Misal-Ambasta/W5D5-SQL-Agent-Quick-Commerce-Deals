"""
Comprehensive test suite for query accuracy validation.
Tests all sample query types with expected results and performance validation.
Task 8.2 implementation.
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import List, Dict

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import SessionLocal
from app.services.query_accuracy_validator import get_query_accuracy_validator, ValidationResult
from app.services.sample_query_handlers import get_sample_query_handlers


class QueryAccuracyTestSuite:
    """Comprehensive test suite for query accuracy validation."""
    
    def __init__(self):
        self.validator = get_query_accuracy_validator()
        self.handlers = get_sample_query_handlers()
        self.test_results = []
    
    async def run_all_tests(self):
        """Run all accuracy validation tests."""
        print("Query Accuracy Validation Test Suite")
        print("=" * 60)
        
        db = SessionLocal()
        
        try:
            # Run individual query tests
            await self._test_individual_queries(db)
            
            # Run regression tests
            await self._test_regression_suite(db)
            
            # Run performance tests
            await self._test_performance_benchmarks(db)
            
            # Generate summary report
            self._generate_summary_report()
            
        except Exception as e:
            print(f"Test suite execution error: {str(e)}")
        finally:
            db.close()
    
    async def _test_individual_queries(self, db):
        """Test individual query types with accuracy validation."""
        print("\n1. Individual Query Accuracy Tests")
        print("-" * 40)
        
        test_queries = [
            ("Which app has cheapest onions right now?", "cheapest_product"),
            ("Show products with 30%+ discount on Blinkit", "discount_search"),
            ("Compare fruit prices between Zepto and Instamart", "price_comparison"),
            ("Find best deals for ₹1000 grocery list", "budget_optimization"),
            ("Which app has cheapest milk right now?", "cheapest_product"),
            ("Show products with 20%+ discount", "discount_search"),
            ("Compare rice prices between all platforms", "price_comparison"),
            ("Find best deals for ₹500 grocery list", "budget_optimization"),
        ]
        
        for i, (query, query_type) in enumerate(test_queries, 1):
            print(f"\n{i}. Testing: '{query}'")
            print("   " + "-" * 50)
            
            try:
                # Execute query
                start_time = asyncio.get_event_loop().time()
                
                if query_type == "cheapest_product":
                    results = await self.handlers.handle_cheapest_product_query(db, query)
                elif query_type == "discount_search":
                    results = await self.handlers.handle_discount_query(db, query)
                elif query_type == "price_comparison":
                    results = await self.handlers.handle_price_comparison_query(db, query)
                elif query_type == "budget_optimization":
                    results = await self.handlers.handle_budget_optimization_query(db, query)
                else:
                    results = []
                
                execution_time = asyncio.get_event_loop().time() - start_time
                
                # Validate results
                validation_report = await self.validator.validate_query_results(
                    query, results, query_type, execution_time, db
                )
                
                # Display results
                print(f"   Results: {len(results)} products found")
                print(f"   Execution time: {execution_time:.3f}s")
                print(f"   Validation status: {validation_report.overall_status.value.upper()}")
                
                if validation_report.issues_found:
                    print(f"   Issues found: {len(validation_report.issues_found)}")
                    for issue in validation_report.issues_found[:3]:
                        print(f"     - {issue}")
                    if len(validation_report.issues_found) > 3:
                        print(f"     ... and {len(validation_report.issues_found) - 3} more")
                else:
                    print("   ✓ All validation checks passed")
                
                # Performance metrics
                perf_score = validation_report.performance_metrics.get('performance_score', 0)
                print(f"   Performance score: {perf_score:.1f}/100")
                
                # Store results
                self.test_results.append({
                    'test_type': 'individual',
                    'query': query,
                    'query_type': query_type,
                    'result_count': len(results),
                    'execution_time': execution_time,
                    'validation_status': validation_report.overall_status.value,
                    'issues_count': len(validation_report.issues_found),
                    'performance_score': perf_score
                })
                
            except Exception as e:
                print(f"   ❌ Test failed: {str(e)}")
                self.test_results.append({
                    'test_type': 'individual',
                    'query': query,
                    'query_type': query_type,
                    'result_count': 0,
                    'execution_time': 0,
                    'validation_status': 'error',
                    'issues_count': 1,
                    'performance_score': 0,
                    'error': str(e)
                })
    
    async def _test_regression_suite(self, db):
        """Run regression tests using predefined test cases."""
        print("\n\n2. Regression Test Suite")
        print("-" * 40)
        
        try:
            regression_reports = await self.validator.run_regression_tests(db)
            
            print(f"Executed {len(regression_reports)} regression test cases")
            
            # Analyze results
            passed = sum(1 for r in regression_reports if r.overall_status == ValidationResult.PASS)
            warnings = sum(1 for r in regression_reports if r.overall_status == ValidationResult.WARNING)
            failed = sum(1 for r in regression_reports if r.overall_status == ValidationResult.FAIL)
            
            print(f"Results: {passed} passed, {warnings} warnings, {failed} failed")
            
            # Show detailed results for failed tests
            if failed > 0:
                print("\nFailed test details:")
                for report in regression_reports:
                    if report.overall_status == ValidationResult.FAIL:
                        print(f"  ❌ {report.test_case_id}: {report.query}")
                        for issue in report.issues_found[:2]:
                            print(f"     - {issue}")
            
            # Store regression results
            for report in regression_reports:
                self.test_results.append({
                    'test_type': 'regression',
                    'test_case_id': report.test_case_id,
                    'query': report.query,
                    'result_count': report.result_count,
                    'execution_time': report.execution_time,
                    'validation_status': report.overall_status.value,
                    'issues_count': len(report.issues_found),
                    'performance_score': report.performance_metrics.get('performance_score', 0)
                })
            
        except Exception as e:
            print(f"Regression test suite failed: {str(e)}")
    
    async def _test_performance_benchmarks(self, db):
        """Test performance benchmarks for different query types."""
        print("\n\n3. Performance Benchmark Tests")
        print("-" * 40)
        
        benchmark_queries = [
            ("Which app has cheapest onions right now?", "cheapest_product", 2.0),
            ("Show products with 25%+ discount", "discount_search", 3.0),
            ("Compare milk prices between Blinkit and Zepto", "price_comparison", 2.5),
            ("Find best deals for ₹800 grocery list", "budget_optimization", 4.0),
        ]
        
        performance_results = []
        
        for query, query_type, expected_max_time in benchmark_queries:
            print(f"\nBenchmarking: '{query[:50]}...'")
            
            try:
                # Run query multiple times for average
                execution_times = []
                result_counts = []
                
                for run in range(3):  # 3 runs for average
                    start_time = asyncio.get_event_loop().time()
                    
                    if query_type == "cheapest_product":
                        results = await self.handlers.handle_cheapest_product_query(db, query)
                    elif query_type == "discount_search":
                        results = await self.handlers.handle_discount_query(db, query)
                    elif query_type == "price_comparison":
                        results = await self.handlers.handle_price_comparison_query(db, query)
                    elif query_type == "budget_optimization":
                        results = await self.handlers.handle_budget_optimization_query(db, query)
                    else:
                        results = []
                    
                    execution_time = asyncio.get_event_loop().time() - start_time
                    execution_times.append(execution_time)
                    result_counts.append(len(results))
                
                avg_time = sum(execution_times) / len(execution_times)
                avg_results = sum(result_counts) / len(result_counts)
                
                # Performance evaluation
                performance_status = "PASS" if avg_time <= expected_max_time else "FAIL"
                
                print(f"  Average execution time: {avg_time:.3f}s (expected: ≤{expected_max_time}s)")
                print(f"  Average result count: {avg_results:.1f}")
                print(f"  Performance status: {performance_status}")
                
                performance_results.append({
                    'query': query,
                    'query_type': query_type,
                    'avg_execution_time': avg_time,
                    'expected_max_time': expected_max_time,
                    'avg_result_count': avg_results,
                    'performance_status': performance_status
                })
                
            except Exception as e:
                print(f"  ❌ Benchmark failed: {str(e)}")
                performance_results.append({
                    'query': query,
                    'query_type': query_type,
                    'avg_execution_time': 0,
                    'expected_max_time': expected_max_time,
                    'avg_result_count': 0,
                    'performance_status': 'ERROR',
                    'error': str(e)
                })
        
        # Performance summary
        passed_benchmarks = sum(1 for r in performance_results if r['performance_status'] == 'PASS')
        print(f"\nPerformance Summary: {passed_benchmarks}/{len(performance_results)} benchmarks passed")
        
        # Store performance results
        self.test_results.extend([{
            'test_type': 'performance',
            **result
        } for result in performance_results])
    
    def _generate_summary_report(self):
        """Generate comprehensive summary report."""
        print("\n\n" + "=" * 60)
        print("QUERY ACCURACY VALIDATION SUMMARY REPORT")
        print("=" * 60)
        
        # Overall statistics
        total_tests = len(self.test_results)
        individual_tests = [r for r in self.test_results if r['test_type'] == 'individual']
        regression_tests = [r for r in self.test_results if r['test_type'] == 'regression']
        performance_tests = [r for r in self.test_results if r['test_type'] == 'performance']
        
        print(f"\nTest Execution Summary:")
        print(f"  Total tests executed: {total_tests}")
        print(f"  Individual query tests: {len(individual_tests)}")
        print(f"  Regression tests: {len(regression_tests)}")
        print(f"  Performance benchmarks: {len(performance_tests)}")
        
        # Validation status summary
        validation_statuses = {}
        for result in self.test_results:
            if 'validation_status' in result:
                status = result['validation_status']
                validation_statuses[status] = validation_statuses.get(status, 0) + 1
        
        print(f"\nValidation Status Distribution:")
        for status, count in validation_statuses.items():
            print(f"  {status.upper()}: {count}")
        
        # Performance summary
        performance_scores = [r.get('performance_score', 0) for r in self.test_results if 'performance_score' in r]
        if performance_scores:
            avg_performance = sum(performance_scores) / len(performance_scores)
            print(f"\nPerformance Metrics:")
            print(f"  Average performance score: {avg_performance:.1f}/100")
            print(f"  Best performance score: {max(performance_scores):.1f}/100")
            print(f"  Worst performance score: {min(performance_scores):.1f}/100")
        
        # Query type analysis
        query_types = {}
        for result in individual_tests:
            qtype = result.get('query_type', 'unknown')
            if qtype not in query_types:
                query_types[qtype] = {'count': 0, 'avg_time': 0, 'avg_results': 0}
            
            query_types[qtype]['count'] += 1
            query_types[qtype]['avg_time'] += result.get('execution_time', 0)
            query_types[qtype]['avg_results'] += result.get('result_count', 0)
        
        print(f"\nQuery Type Performance:")
        for qtype, stats in query_types.items():
            count = stats['count']
            avg_time = stats['avg_time'] / count if count > 0 else 0
            avg_results = stats['avg_results'] / count if count > 0 else 0
            print(f"  {qtype}: {avg_time:.3f}s avg, {avg_results:.1f} results avg")
        
        # Issues summary
        total_issues = sum(r.get('issues_count', 0) for r in self.test_results)
        print(f"\nIssues Summary:")
        print(f"  Total issues found: {total_issues}")
        
        # Save detailed report to file
        self._save_detailed_report()
        
        print(f"\n{'='*60}")
        print("Query accuracy validation completed!")
        print("Detailed report saved to 'query_accuracy_report.json'")
    
    def _save_detailed_report(self):
        """Save detailed test results to JSON file."""
        report_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'total_tests': len(self.test_results),
                'test_types': {
                    'individual': len([r for r in self.test_results if r['test_type'] == 'individual']),
                    'regression': len([r for r in self.test_results if r['test_type'] == 'regression']),
                    'performance': len([r for r in self.test_results if r['test_type'] == 'performance'])
                }
            },
            'test_results': self.test_results
        }
        
        try:
            with open('query_accuracy_report.json', 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save detailed report: {str(e)}")


async def main():
    """Main test execution function."""
    test_suite = QueryAccuracyTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())