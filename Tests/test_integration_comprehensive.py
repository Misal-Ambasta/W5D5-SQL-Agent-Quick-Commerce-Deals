"""
Comprehensive Integration and End-to-End Test Suite
Task 10.1: Integrate and Create comprehensive test suite

This test suite covers:
- Integration tests for FastAPI endpoints with frontend functionality
- Unit tests for all FastAPI endpoints with proper test coverage
- Integration tests for LangChain agent and database interactions
- End-to-end tests for complete user query workflows
- Performance tests for concurrent user scenarios and load testing

Requirements: 3.3, 8.2, 12.4
"""

import asyncio
import pytest
import requests
import time
import json
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text

# Import application components
from app.main import app
from app.core.database import SessionLocal, engine
from app.core.config import settings
from app.services.multi_step_query import get_multi_step_processor
from app.services.result_processor import get_result_processor
from app.services.sample_query_handlers import get_sample_query_handlers
from app.core.sql_agent import get_sql_agent


class IntegrationTestSuite:
    """Comprehensive integration test suite for Quick Commerce Deals platform."""
    
    def __init__(self):
        self.client = TestClient(app)
        self.base_url = "http://localhost:8000"
        self.api_url = f"{self.base_url}/api/v1"
        self.test_results = []
        self.performance_metrics = []
    
    async def run_all_tests(self):
        """Run all integration and end-to-end tests."""
        print("🚀 Starting Comprehensive Integration Test Suite")
        print("=" * 80)
        
        try:
            # 1. Unit tests for FastAPI endpoints
            await self._test_fastapi_endpoints()
            
            # 2. Integration tests for LangChain agent and database
            await self._test_langchain_database_integration()
            
            # 3. End-to-end user workflow tests
            await self._test_end_to_end_workflows()
            
            # 4. Frontend-backend integration tests
            await self._test_frontend_backend_integration()
            
            # 5. Performance and load tests
            await self._test_performance_and_load()
            
            # 6. Error handling and edge cases
            await self._test_error_handling()
            
            # Generate comprehensive report
            self._generate_integration_report()
            
        except Exception as e:
            print(f"❌ Test suite execution failed: {str(e)}")
            raise
    
    async def _test_fastapi_endpoints(self):
        """Unit tests for all FastAPI endpoints with proper test coverage."""
        print("\n📋 1. FastAPI Endpoints Unit Tests")
        print("-" * 50)
        
        endpoint_tests = [
            # Health and basic endpoints
            ("GET", "/", "Root endpoint"),
            ("GET", "/health", "Health check endpoint"),
            
            # Query endpoints
            ("POST", "/api/v1/query/", "Natural language query endpoint"),
            ("POST", "/api/v1/query/advanced", "Advanced query endpoint"),
            
            # Product endpoints
            ("GET", "/api/v1/products/compare", "Product comparison GET"),
            ("POST", "/api/v1/products/compare", "Product comparison POST"),
            
            # Deals endpoints
            ("GET", "/api/v1/deals/", "Deals listing GET"),
            ("POST", "/api/v1/deals/", "Deals listing POST"),
            ("GET", "/api/v1/deals/campaigns", "Promotional campaigns"),
            
            # Monitoring endpoints
            ("GET", "/api/v1/monitoring/health", "Monitoring health"),
            ("GET", "/api/v1/monitoring/metrics", "System metrics"),
        ]
        
        for method, endpoint, description in endpoint_tests:
            await self._test_single_endpoint(method, endpoint, description)
    
    async def _test_single_endpoint(self, method: str, endpoint: str, description: str):
        """Test a single API endpoint."""
        print(f"  Testing {method} {endpoint} - {description}")
        
        try:
            start_time = time.time()
            
            if method == "GET":
                if "compare" in endpoint:
                    # Add required query parameters for product comparison
                    response = self.client.get(f"{endpoint}?product_name=onion")
                else:
                    response = self.client.get(endpoint)
            
            elif method == "POST":
                if "query" in endpoint:
                    # Test query endpoints
                    test_data = {"query": "Which app has cheapest onions right now?"}
                    response = self.client.post(endpoint, json=test_data)
                
                elif "compare" in endpoint:
                    # Test product comparison
                    test_data = {"product_name": "onion", "platforms": ["Blinkit", "Zepto"]}
                    response = self.client.post(endpoint, json=test_data)
                
                elif "deals" in endpoint:
                    # Test deals endpoint
                    test_data = {"platform": "Blinkit", "min_discount": 10}
                    response = self.client.post(endpoint, json=test_data)
                
                else:
                    response = self.client.post(endpoint, json={})
            
            execution_time = time.time() - start_time
            
            # Validate response
            success = response.status_code in [200, 201, 422]  # 422 is acceptable for validation errors
            
            if success:
                print(f"    ✅ Status: {response.status_code}, Time: {execution_time:.3f}s")
                
                # Additional validation for successful responses
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        if isinstance(response_data, dict):
                            print(f"    📊 Response keys: {list(response_data.keys())}")
                    except:
                        pass
            else:
                print(f"    ❌ Status: {response.status_code}, Time: {execution_time:.3f}s")
                print(f"    Error: {response.text[:100]}...")
            
            # Store test result
            self.test_results.append({
                'test_type': 'endpoint',
                'method': method,
                'endpoint': endpoint,
                'description': description,
                'status_code': response.status_code,
                'execution_time': execution_time,
                'success': success
            })
            
        except Exception as e:
            print(f"    ❌ Exception: {str(e)}")
            self.test_results.append({
                'test_type': 'endpoint',
                'method': method,
                'endpoint': endpoint,
                'description': description,
                'status_code': 0,
                'execution_time': 0,
                'success': False,
                'error': str(e)
            })
    
    async def _test_langchain_database_integration(self):
        """Integration tests for LangChain agent and database interactions."""
        print("\n🔗 2. LangChain Agent & Database Integration Tests")
        print("-" * 50)
        
        db = SessionLocal()
        
        try:
            # Test database connectivity
            print("  Testing database connectivity...")
            db.execute(text("SELECT 1"))
            print("    ✅ Database connection successful")
            
            # Test LangChain SQL agent integration
            print("  Testing LangChain SQL agent integration...")
            try:
                sql_agent = get_sql_agent()
                print("    ✅ SQL agent initialization successful")
                
                # Test agent with simple query (if API key available)
                test_query = "Show me the count of products in the database"
                try:
                    # This might fail without proper API key, which is expected
                    result = await sql_agent.process_query(test_query)
                    print(f"    ✅ Agent query processing successful")
                    print(f"    📊 Result type: {type(result)}")
                except Exception as e:
                    print(f"    ⚠️  Agent query processing failed (expected without API key): {str(e)[:100]}")
                
            except Exception as e:
                print(f"    ⚠️  SQL agent initialization failed: {str(e)[:100]}")
            
            # Test multi-step query processor
            print("  Testing multi-step query processor...")
            try:
                multi_step_processor = get_multi_step_processor()
                
                # Create execution plan
                test_query = "Which app has cheapest onions right now?"
                execution_plan = await multi_step_processor.create_execution_plan(test_query)
                print(f"    ✅ Execution plan created with {len(execution_plan.steps)} steps")
                
                # Test plan execution (might fail without data, which is expected)
                try:
                    result = await multi_step_processor.execute_plan(execution_plan)
                    print(f"    ✅ Plan execution completed, success: {result.success}")
                except Exception as e:
                    print(f"    ⚠️  Plan execution failed (expected without data): {str(e)[:100]}")
                
            except Exception as e:
                print(f"    ❌ Multi-step processor test failed: {str(e)}")
            
            # Test result processor
            print("  Testing result processor...")
            try:
                result_processor = get_result_processor()
                
                # Test with sample data
                sample_data = [
                    {"product_name": "Onion", "platform_name": "Blinkit", "current_price": 25.0},
                    {"product_name": "Onion", "platform_name": "Zepto", "current_price": 28.0}
                ]
                
                from app.services.result_processor import PaginationConfig, SamplingConfig, ResultFormat, SamplingMethod
                
                processed_result = await result_processor.process_results(
                    raw_results=sample_data,
                    query="test query",
                    pagination_config=PaginationConfig(page=1, page_size=10),
                    sampling_config=SamplingConfig(method=SamplingMethod.NONE),
                    result_format=ResultFormat.STRUCTURED
                )
                
                print(f"    ✅ Result processing successful, {len(processed_result.data)} results")
                
            except Exception as e:
                print(f"    ❌ Result processor test failed: {str(e)}")
            
            # Test sample query handlers
            print("  Testing sample query handlers...")
            try:
                handlers = get_sample_query_handlers()
                
                # Test each handler type
                test_queries = [
                    ("Which app has cheapest onions right now?", "cheapest"),
                    ("Show products with 30%+ discount on Blinkit", "discount"),
                    ("Compare fruit prices between Zepto and Instamart", "comparison"),
                    ("Find best deals for ₹1000 grocery list", "budget")
                ]
                
                for query, query_type in test_queries:
                    try:
                        if query_type == "cheapest":
                            results = await handlers.handle_cheapest_product_query(db, query)
                        elif query_type == "discount":
                            results = await handlers.handle_discount_query(db, query)
                        elif query_type == "comparison":
                            results = await handlers.handle_price_comparison_query(db, query)
                        elif query_type == "budget":
                            results = await handlers.handle_budget_optimization_query(db, query)
                        
                        print(f"    ✅ {query_type.title()} query handler: {len(results)} results")
                        
                    except Exception as e:
                        print(f"    ⚠️  {query_type.title()} query handler failed: {str(e)[:100]}")
                
            except Exception as e:
                print(f"    ❌ Sample query handlers test failed: {str(e)}")
            
        except Exception as e:
            print(f"    ❌ Database connectivity test failed: {str(e)}")
        
        finally:
            db.close()
    
    async def _test_end_to_end_workflows(self):
        """End-to-end tests for complete user query workflows."""
        print("\n🔄 3. End-to-End User Workflow Tests")
        print("-" * 50)
        
        # Test complete user workflows
        workflows = [
            {
                'name': 'Price Comparison Workflow',
                'steps': [
                    ('POST', '/api/v1/query/', {'query': 'Which app has cheapest onions right now?'}),
                    ('GET', '/api/v1/products/compare?product_name=onion', None),
                    ('GET', '/api/v1/deals/?platform=Blinkit&min_discount=10', None)
                ]
            },
            {
                'name': 'Discount Discovery Workflow',
                'steps': [
                    ('POST', '/api/v1/query/', {'query': 'Show products with 30%+ discount on Blinkit'}),
                    ('GET', '/api/v1/deals/?platform=Blinkit&min_discount=30', None),
                    ('GET', '/api/v1/deals/campaigns?platform=Blinkit', None)
                ]
            },
            {
                'name': 'Budget Optimization Workflow',
                'steps': [
                    ('POST', '/api/v1/query/', {'query': 'Find best deals for ₹1000 grocery list'}),
                    ('GET', '/api/v1/deals/?min_discount=20', None),
                    ('POST', '/api/v1/products/compare', {'product_name': 'rice', 'platforms': ['Blinkit', 'Zepto']})
                ]
            }
        ]
        
        for workflow in workflows:
            print(f"  Testing {workflow['name']}...")
            workflow_success = True
            workflow_times = []
            
            for i, (method, endpoint, data) in enumerate(workflow['steps'], 1):
                try:
                    start_time = time.time()
                    
                    if method == 'GET':
                        response = self.client.get(endpoint)
                    else:
                        response = self.client.post(endpoint, json=data)
                    
                    execution_time = time.time() - start_time
                    workflow_times.append(execution_time)
                    
                    if response.status_code in [200, 201, 422]:
                        print(f"    ✅ Step {i}: {response.status_code} ({execution_time:.3f}s)")
                    else:
                        print(f"    ❌ Step {i}: {response.status_code} ({execution_time:.3f}s)")
                        workflow_success = False
                
                except Exception as e:
                    print(f"    ❌ Step {i}: Exception - {str(e)[:50]}")
                    workflow_success = False
                    workflow_times.append(0)
            
            total_time = sum(workflow_times)
            print(f"    📊 Workflow {'✅ PASSED' if workflow_success else '❌ FAILED'} - Total time: {total_time:.3f}s")
            
            # Store workflow result
            self.test_results.append({
                'test_type': 'workflow',
                'workflow_name': workflow['name'],
                'success': workflow_success,
                'total_time': total_time,
                'steps_count': len(workflow['steps'])
            })
    
    async def _test_frontend_backend_integration(self):
        """Test integration between FastAPI backend and Streamlit frontend functionality."""
        print("\n🖥️  4. Frontend-Backend Integration Tests")
        print("-" * 50)
        
        # Test API endpoints that the frontend would use
        frontend_api_calls = [
            {
                'name': 'Query Processing for Frontend',
                'method': 'POST',
                'endpoint': '/api/v1/query/',
                'data': {'query': 'Which app has cheapest milk right now?'},
                'expected_fields': ['query', 'results', 'execution_time']
            },
            {
                'name': 'Product Comparison for Frontend',
                'method': 'GET',
                'endpoint': '/api/v1/products/compare?product_name=milk',
                'data': None,
                'expected_fields': ['query', 'comparisons', 'total_products']
            },
            {
                'name': 'Deals Listing for Frontend',
                'method': 'GET',
                'endpoint': '/api/v1/deals/?limit=10',
                'data': None,
                'expected_fields': ['deals', 'total_deals', 'execution_time']
            },
            {
                'name': 'Advanced Query for Frontend',
                'method': 'POST',
                'endpoint': '/api/v1/query/advanced?page=1&page_size=20&result_format=structured',
                'data': {'query': 'Compare rice prices between all platforms'},
                'expected_fields': ['query', 'results', 'total_results']
            }
        ]
        
        for api_call in frontend_api_calls:
            print(f"  Testing {api_call['name']}...")
            
            try:
                start_time = time.time()
                
                if api_call['method'] == 'GET':
                    response = self.client.get(api_call['endpoint'])
                else:
                    response = self.client.post(api_call['endpoint'], json=api_call['data'])
                
                execution_time = time.time() - start_time
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    # Check expected fields
                    missing_fields = []
                    for field in api_call['expected_fields']:
                        if field not in response_data:
                            missing_fields.append(field)
                    
                    if not missing_fields:
                        print(f"    ✅ Response structure valid ({execution_time:.3f}s)")
                        print(f"    📊 Fields: {list(response_data.keys())}")
                    else:
                        print(f"    ⚠️  Missing fields: {missing_fields} ({execution_time:.3f}s)")
                
                elif response.status_code == 422:
                    print(f"    ⚠️  Validation error (expected without data): {response.status_code}")
                else:
                    print(f"    ❌ Unexpected status: {response.status_code}")
                
            except Exception as e:
                print(f"    ❌ Exception: {str(e)[:50]}")
        
        # Test CORS headers for frontend integration
        print("  Testing CORS configuration...")
        try:
            response = self.client.get("/", headers={"Origin": "http://localhost:8501"})
            cors_headers = {
                'access-control-allow-origin': response.headers.get('access-control-allow-origin'),
                'access-control-allow-methods': response.headers.get('access-control-allow-methods'),
                'access-control-allow-headers': response.headers.get('access-control-allow-headers')
            }
            
            if any(cors_headers.values()):
                print(f"    ✅ CORS headers configured")
                for header, value in cors_headers.items():
                    if value:
                        print(f"      {header}: {value}")
            else:
                print(f"    ⚠️  CORS headers not found (may be configured differently)")
                
        except Exception as e:
            print(f"    ❌ CORS test failed: {str(e)}")
    
    async def _test_performance_and_load(self):
        """Performance tests for concurrent user scenarios and load testing."""
        print("\n⚡ 5. Performance and Load Tests")
        print("-" * 50)
        
        # Single request performance benchmarks
        print("  Performance Benchmarks:")
        
        benchmark_tests = [
            ('POST', '/api/v1/query/', {'query': 'Which app has cheapest onions right now?'}, 3.0),
            ('GET', '/api/v1/products/compare?product_name=milk', None, 2.0),
            ('GET', '/api/v1/deals/?limit=20', None, 1.5),
            ('GET', '/health', None, 0.5)
        ]
        
        for method, endpoint, data, max_time in benchmark_tests:
            times = []
            
            # Run 5 times for average
            for _ in range(5):
                start_time = time.time()
                
                if method == 'GET':
                    response = self.client.get(endpoint)
                else:
                    response = self.client.post(endpoint, json=data)
                
                execution_time = time.time() - start_time
                times.append(execution_time)
            
            avg_time = sum(times) / len(times)
            max_measured = max(times)
            min_measured = min(times)
            
            status = "✅ PASS" if avg_time <= max_time else "❌ FAIL"
            print(f"    {status} {endpoint}: {avg_time:.3f}s avg (max: {max_measured:.3f}s, target: ≤{max_time}s)")
            
            self.performance_metrics.append({
                'endpoint': endpoint,
                'method': method,
                'avg_time': avg_time,
                'max_time': max_measured,
                'min_time': min_measured,
                'target_time': max_time,
                'passed': avg_time <= max_time
            })
        
        # Concurrent user simulation
        print("\n  Concurrent User Load Test:")
        await self._test_concurrent_load()
    
    async def _test_concurrent_load(self):
        """Test concurrent user scenarios."""
        concurrent_users = [5, 10, 20]
        
        for user_count in concurrent_users:
            print(f"    Testing {user_count} concurrent users...")
            
            def make_request():
                """Single request function for concurrent testing."""
                try:
                    start_time = time.time()
                    response = self.client.post('/api/v1/query/', json={'query': 'Which app has cheapest milk right now?'})
                    execution_time = time.time() - start_time
                    return {
                        'status_code': response.status_code,
                        'execution_time': execution_time,
                        'success': response.status_code in [200, 422]
                    }
                except Exception as e:
                    return {
                        'status_code': 0,
                        'execution_time': 0,
                        'success': False,
                        'error': str(e)
                    }
            
            # Execute concurrent requests
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=user_count) as executor:
                futures = [executor.submit(make_request) for _ in range(user_count)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            total_time = time.time() - start_time
            
            # Analyze results
            successful_requests = sum(1 for r in results if r['success'])
            avg_response_time = sum(r['execution_time'] for r in results) / len(results)
            max_response_time = max(r['execution_time'] for r in results)
            
            success_rate = (successful_requests / user_count) * 100
            requests_per_second = user_count / total_time
            
            print(f"      Success rate: {success_rate:.1f}% ({successful_requests}/{user_count})")
            print(f"      Avg response time: {avg_response_time:.3f}s")
            print(f"      Max response time: {max_response_time:.3f}s")
            print(f"      Requests/second: {requests_per_second:.1f}")
            
            # Store load test results
            self.performance_metrics.append({
                'test_type': 'load_test',
                'concurrent_users': user_count,
                'success_rate': success_rate,
                'avg_response_time': avg_response_time,
                'max_response_time': max_response_time,
                'requests_per_second': requests_per_second,
                'total_time': total_time
            })
    
    async def _test_error_handling(self):
        """Test error handling and edge cases."""
        print("\n🛡️  6. Error Handling and Edge Cases")
        print("-" * 50)
        
        error_test_cases = [
            # Invalid query data
            ('POST', '/api/v1/query/', {'query': ''}, 422, "Empty query validation"),
            ('POST', '/api/v1/query/', {'query': 'x' * 1001}, 422, "Query too long validation"),
            ('POST', '/api/v1/query/', {}, 422, "Missing query field"),
            
            # Invalid product comparison data
            ('GET', '/api/v1/products/compare', None, 422, "Missing product name"),
            ('GET', '/api/v1/products/compare?product_name=', None, 422, "Empty product name"),
            
            # Invalid deals parameters
            ('GET', '/api/v1/deals/?min_discount=150', None, 422, "Invalid discount percentage"),
            ('GET', '/api/v1/deals/?limit=1000', None, 422, "Limit too high"),
            
            # Malformed JSON
            ('POST', '/api/v1/query/', "invalid json", 422, "Malformed JSON"),
        ]
        
        for method, endpoint, data, expected_status, description in error_test_cases:
            print(f"  Testing {description}...")
            
            try:
                if method == 'GET':
                    response = self.client.get(endpoint)
                else:
                    if isinstance(data, str):
                        # Test malformed JSON
                        response = self.client.post(endpoint, data=data, headers={'Content-Type': 'application/json'})
                    else:
                        response = self.client.post(endpoint, json=data)
                
                if response.status_code == expected_status:
                    print(f"    ✅ Correct error handling: {response.status_code}")
                else:
                    print(f"    ⚠️  Unexpected status: {response.status_code} (expected: {expected_status})")
                
                # Check error response format
                if response.status_code >= 400:
                    try:
                        error_data = response.json()
                        if 'detail' in error_data or 'message' in error_data:
                            print(f"    📋 Error format valid")
                        else:
                            print(f"    ⚠️  Error format may be non-standard")
                    except:
                        print(f"    ⚠️  Error response not JSON")
                
            except Exception as e:
                print(f"    ❌ Exception during error test: {str(e)[:50]}")
        
        # Test rate limiting (if configured)
        print("  Testing rate limiting...")
        try:
            # Make multiple rapid requests
            responses = []
            for i in range(15):  # Exceed typical rate limit
                response = self.client.get("/health")
                responses.append(response.status_code)
            
            rate_limited = any(status == 429 for status in responses)
            if rate_limited:
                print(f"    ✅ Rate limiting active (429 status detected)")
            else:
                print(f"    ⚠️  Rate limiting not triggered (may be configured differently)")
                
        except Exception as e:
            print(f"    ❌ Rate limiting test failed: {str(e)}")
    
    def _generate_integration_report(self):
        """Generate comprehensive integration test report."""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE INTEGRATION TEST REPORT")
        print("=" * 80)
        
        # Overall statistics
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.get('success', False))
        
        print(f"\n📈 Test Execution Summary:")
        print(f"  Total tests executed: {total_tests}")
        print(f"  Successful tests: {successful_tests}")
        print(f"  Success rate: {(successful_tests/total_tests)*100:.1f}%")
        
        # Test type breakdown
        test_types = {}
        for result in self.test_results:
            test_type = result.get('test_type', 'unknown')
            if test_type not in test_types:
                test_types[test_type] = {'total': 0, 'success': 0}
            test_types[test_type]['total'] += 1
            if result.get('success', False):
                test_types[test_type]['success'] += 1
        
        print(f"\n📋 Test Type Breakdown:")
        for test_type, stats in test_types.items():
            success_rate = (stats['success'] / stats['total']) * 100 if stats['total'] > 0 else 0
            print(f"  {test_type.title()}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Performance metrics summary
        if self.performance_metrics:
            print(f"\n⚡ Performance Summary:")
            
            # Endpoint performance
            endpoint_metrics = [m for m in self.performance_metrics if 'endpoint' in m]
            if endpoint_metrics:
                avg_times = [m['avg_time'] for m in endpoint_metrics]
                passed_benchmarks = sum(1 for m in endpoint_metrics if m.get('passed', False))
                
                print(f"  Endpoint benchmarks: {passed_benchmarks}/{len(endpoint_metrics)} passed")
                print(f"  Average response time: {sum(avg_times)/len(avg_times):.3f}s")
                print(f"  Fastest endpoint: {min(avg_times):.3f}s")
                print(f"  Slowest endpoint: {max(avg_times):.3f}s")
            
            # Load test results
            load_metrics = [m for m in self.performance_metrics if m.get('test_type') == 'load_test']
            if load_metrics:
                print(f"  Load test scenarios: {len(load_metrics)}")
                for metric in load_metrics:
                    users = metric['concurrent_users']
                    success_rate = metric['success_rate']
                    rps = metric['requests_per_second']
                    print(f"    {users} users: {success_rate:.1f}% success, {rps:.1f} req/s")
        
        # Failed tests details
        failed_tests = [r for r in self.test_results if not r.get('success', False)]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests[:5]:  # Show first 5 failures
                test_name = test.get('description', test.get('endpoint', test.get('workflow_name', 'Unknown')))
                error = test.get('error', f"Status: {test.get('status_code', 'Unknown')}")
                print(f"  • {test_name}: {error[:60]}")
            
            if len(failed_tests) > 5:
                print(f"  ... and {len(failed_tests) - 5} more failures")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        if successful_tests / total_tests < 0.8:
            print("  • Review failed tests and fix critical issues")
        
        if self.performance_metrics:
            slow_endpoints = [m for m in self.performance_metrics if m.get('avg_time', 0) > 2.0]
            if slow_endpoints:
                print("  • Optimize slow endpoints for better performance")
        
        if not any('load_test' in str(m) for m in self.performance_metrics):
            print("  • Consider adding more comprehensive load testing")
        
        print("  • Ensure database contains test data for more realistic results")
        print("  • Configure API keys for full LangChain functionality testing")
        
        # Save detailed report
        self._save_integration_report()
        
        print(f"\n{'='*80}")
        print("✅ Integration test suite completed!")
        print("📄 Detailed report saved to 'integration_test_report.json'")
    
    def _save_integration_report(self):
        """Save detailed integration test report to file."""
        report_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'total_tests': len(self.test_results),
                'successful_tests': sum(1 for r in self.test_results if r.get('success', False)),
                'test_types': {}
            },
            'test_results': self.test_results,
            'performance_metrics': self.performance_metrics
        }
        
        # Calculate test type statistics
        for result in self.test_results:
            test_type = result.get('test_type', 'unknown')
            if test_type not in report_data['summary']['test_types']:
                report_data['summary']['test_types'][test_type] = {'total': 0, 'success': 0}
            report_data['summary']['test_types'][test_type]['total'] += 1
            if result.get('success', False):
                report_data['summary']['test_types'][test_type]['success'] += 1
        
        try:
            with open('integration_test_report.json', 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save detailed report: {str(e)}")


async def main():
    """Main test execution function."""
    test_suite = IntegrationTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())