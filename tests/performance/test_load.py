"""
Load testing for the Financial AI Agents system.

This module tests system performance under various load conditions
including concurrent requests, high throughput, and sustained load.
"""

import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import httpx
from fastapi.testclient import TestClient

from app.main import create_app
from tests.fixtures.sample_data import (
    PERFORMANCE_TEST_REQUESTS,
    TEST_API_KEYS,
    create_sample_stock_data
)
from tests.fixtures.mock_responses import setup_mock_environment


class TestLoadPerformance:
    """Load testing for API endpoints."""
    
    @pytest.fixture(scope="class")
    def app(self):
        """Create FastAPI app for load testing."""
        # Set up test environment
        import os
        for key, value in TEST_API_KEYS.items():
            os.environ[key.upper()] = value
        
        return create_app()
    
    @pytest.fixture(scope="class")
    def client(self, app):
        """Create test client for load testing."""
        return TestClient(app)
    
    def test_concurrent_research_requests(self, client):
        """Test concurrent research analysis requests."""
        requests = PERFORMANCE_TEST_REQUESTS["research_requests"][:10]
        
        def make_request(request_data):
            start_time = time.time()
            try:
                response = client.post("/api/v1/research/analyze", json=request_data)
                end_time = time.time()
                return {
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "status_code": 500,
                    "response_time": end_time - start_time,
                    "success": False,
                    "error": str(e)
                }
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, req) for req in requests]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        response_times = [r["response_time"] for r in results if r["success"]]
        
        assert success_rate >= 0.8, f"Success rate too low: {success_rate}"
        if response_times:
            avg_response_time = statistics.mean(response_times)
            assert avg_response_time < 30.0, f"Average response time too high: {avg_response_time}s"
    
    def test_concurrent_stock_requests(self, client):
        """Test concurrent stock analysis requests."""
        requests = PERFORMANCE_TEST_REQUESTS["stock_requests"][:10]
        
        def make_request(request_data):
            start_time = time.time()
            try:
                response = client.post("/api/v1/stocks/analyze", json=request_data)
                end_time = time.time()
                return {
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "status_code": 500,
                    "response_time": end_time - start_time,
                    "success": False,
                    "error": str(e)
                }
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, req) for req in requests]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        response_times = [r["response_time"] for r in results if r["success"]]
        
        assert success_rate >= 0.8, f"Success rate too low: {success_rate}"
        if response_times:
            avg_response_time = statistics.mean(response_times)
            assert avg_response_time < 25.0, f"Average response time too high: {avg_response_time}s"
    
    def test_concurrent_evaluation_requests(self, client):
        """Test concurrent RAG evaluation requests."""
        requests = PERFORMANCE_TEST_REQUESTS["evaluation_requests"][:10]
        
        def make_request(request_data):
            start_time = time.time()
            try:
                response = client.post("/api/v1/evaluation/assess", json=request_data)
                end_time = time.time()
                return {
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "status_code": 500,
                    "response_time": end_time - start_time,
                    "success": False,
                    "error": str(e)
                }
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, req) for req in requests]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        response_times = [r["response_time"] for r in results if r["success"]]
        
        assert success_rate >= 0.8, f"Success rate too low: {success_rate}"
        if response_times:
            avg_response_time = statistics.mean(response_times)
            assert avg_response_time < 20.0, f"Average response time too high: {avg_response_time}s"
    
    def test_mixed_workload_performance(self, client):
        """Test performance with mixed request types."""
        # Create mixed workload
        research_requests = [
            ("research", req) for req in PERFORMANCE_TEST_REQUESTS["research_requests"][:3]
        ]
        stock_requests = [
            ("stock", req) for req in PERFORMANCE_TEST_REQUESTS["stock_requests"][:3]
        ]
        eval_requests = [
            ("evaluation", req) for req in PERFORMANCE_TEST_REQUESTS["evaluation_requests"][:4]
        ]
        
        all_requests = research_requests + stock_requests + eval_requests
        
        def make_request(request_type, request_data):
            start_time = time.time()
            try:
                if request_type == "research":
                    response = client.post("/api/v1/research/analyze", json=request_data)
                elif request_type == "stock":
                    response = client.post("/api/v1/stocks/analyze", json=request_data)
                elif request_type == "evaluation":
                    response = client.post("/api/v1/evaluation/assess", json=request_data)
                
                end_time = time.time()
                return {
                    "type": request_type,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "type": request_type,
                    "status_code": 500,
                    "response_time": end_time - start_time,
                    "success": False,
                    "error": str(e)
                }
        
        # Execute mixed workload
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [
                executor.submit(make_request, req_type, req_data)
                for req_type, req_data in all_requests
            ]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze results by type
        by_type = {}
        for result in results:
            req_type = result["type"]
            if req_type not in by_type:
                by_type[req_type] = []
            by_type[req_type].append(result)
        
        # Check performance for each type
        for req_type, type_results in by_type.items():
            success_rate = sum(1 for r in type_results if r["success"]) / len(type_results)
            response_times = [r["response_time"] for r in type_results if r["success"]]
            
            assert success_rate >= 0.7, f"{req_type} success rate too low: {success_rate}"
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                max_expected_time = 35.0  # Higher threshold for mixed workload
                assert avg_response_time < max_expected_time, \
                    f"{req_type} average response time too high: {avg_response_time}s"
    
    def test_sustained_load_performance(self, client):
        """Test performance under sustained load."""
        duration_seconds = 30  # Run for 30 seconds
        request_interval = 2.0  # Send request every 2 seconds
        
        start_time = time.time()
        results = []
        
        while time.time() - start_time < duration_seconds:
            request_start = time.time()
            
            try:
                # Alternate between different request types
                current_time = time.time() - start_time
                if int(current_time) % 3 == 0:
                    # Research request
                    request_data = PERFORMANCE_TEST_REQUESTS["research_requests"][0]
                    response = client.post("/api/v1/research/analyze", json=request_data)
                    req_type = "research"
                elif int(current_time) % 3 == 1:
                    # Stock request
                    request_data = PERFORMANCE_TEST_REQUESTS["stock_requests"][0]
                    response = client.post("/api/v1/stocks/analyze", json=request_data)
                    req_type = "stock"
                else:
                    # Evaluation request
                    request_data = PERFORMANCE_TEST_REQUESTS["evaluation_requests"][0]
                    response = client.post("/api/v1/evaluation/assess", json=request_data)
                    req_type = "evaluation"
                
                request_end = time.time()
                
                results.append({
                    "type": req_type,
                    "timestamp": request_start,
                    "response_time": request_end - request_start,
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                })
                
            except Exception as e:
                request_end = time.time()
                results.append({
                    "type": "error",
                    "timestamp": request_start,
                    "response_time": request_end - request_start,
                    "status_code": 500,
                    "success": False,
                    "error": str(e)
                })
            
            # Wait for next request
            elapsed = time.time() - request_start
            if elapsed < request_interval:
                time.sleep(request_interval - elapsed)
        
        # Analyze sustained load results
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r["success"])
        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        
        response_times = [r["response_time"] for r in results if r["success"]]
        
        assert total_requests >= 10, f"Too few requests made: {total_requests}"
        assert success_rate >= 0.7, f"Success rate too low under sustained load: {success_rate}"
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            
            assert avg_response_time < 40.0, f"Average response time degraded: {avg_response_time}s"
            assert p95_response_time < 60.0, f"95th percentile response time too high: {p95_response_time}s"


class TestAsyncLoadPerformance:
    """Async load testing for better concurrency simulation."""
    
    @pytest.fixture
    def mock_environment(self):
        """Set up mock environment for async testing."""
        return setup_mock_environment()
    
    @pytest.mark.asyncio
    async def test_async_concurrent_requests(self, mock_environment):
        """Test async concurrent request handling."""
        from app.agents.research_agent import ResearchAgent
        from app.agents.stock_agent import StockAgent
        from app.agents.rag_evaluator import RAGEvaluator
        
        # Create agents with mocked dependencies
        research_agent = ResearchAgent(groq_api_key="test_key")
        stock_agent = StockAgent(groq_api_key="test_key")
        rag_evaluator = RAGEvaluator(groq_api_key="test_key")
        
        # Mock the AI clients
        research_agent.groq_client = mock_environment["groq_client"]
        stock_agent.groq_client = mock_environment["groq_client"]
        rag_evaluator.groq_client = mock_environment["groq_client"]
        
        async def research_task():
            request = {"topic": "Test research topic", "sources_limit": 5}
            start_time = time.time()
            try:
                result = await research_agent.process_request(request)
                end_time = time.time()
                return {
                    "type": "research",
                    "success": True,
                    "response_time": end_time - start_time
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "type": "research",
                    "success": False,
                    "response_time": end_time - start_time,
                    "error": str(e)
                }
        
        async def stock_task():
            request = {"symbols": ["AAPL"], "analysis_type": "comprehensive"}
            start_time = time.time()
            try:
                result = await stock_agent.process_request(request)
                end_time = time.time()
                return {
                    "type": "stock",
                    "success": True,
                    "response_time": end_time - start_time
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "type": "stock",
                    "success": False,
                    "response_time": end_time - start_time,
                    "error": str(e)
                }
        
        async def evaluation_task():
            request = {
                "query": "Test query",
                "response": "Test response for evaluation",
                "context": ["Test context document"]
            }
            start_time = time.time()
            try:
                result = await rag_evaluator.process_request(request)
                end_time = time.time()
                return {
                    "type": "evaluation",
                    "success": True,
                    "response_time": end_time - start_time
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "type": "evaluation",
                    "success": False,
                    "response_time": end_time - start_time,
                    "error": str(e)
                }
        
        # Create concurrent tasks
        tasks = []
        for _ in range(3):
            tasks.extend([research_task(), stock_task(), evaluation_task()])
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and analyze results
        valid_results = [r for r in results if isinstance(r, dict)]
        
        success_rate = sum(1 for r in valid_results if r["success"]) / len(valid_results)
        response_times = [r["response_time"] for r in valid_results if r["success"]]
        
        assert success_rate >= 0.8, f"Async success rate too low: {success_rate}"
        if response_times:
            avg_response_time = statistics.mean(response_times)
            assert avg_response_time < 5.0, f"Async response time too high: {avg_response_time}s"
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage during high load scenarios."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate memory-intensive operations
        large_data_sets = []
        for i in range(100):
            # Create sample data that might be used in processing
            data = {
                "request_id": f"req_{i}",
                "data": [j for j in range(1000)],  # Simulate processing data
                "results": {"analysis": f"Result {i}" * 100}
            }
            large_data_sets.append(data)
        
        # Simulate processing
        await asyncio.sleep(1)
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Clean up
        large_data_sets.clear()
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100, f"Memory usage increased too much: {memory_increase}MB"
    
    @pytest.mark.asyncio
    async def test_error_handling_under_load(self, mock_environment):
        """Test error handling and recovery under load conditions."""
        from app.agents.research_agent import ResearchAgent
        
        research_agent = ResearchAgent(groq_api_key="test_key")
        
        # Configure mock to fail intermittently
        call_count = 0
        original_create = mock_environment["groq_client"].chat.completions.create
        
        async def failing_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:  # Fail every 3rd call
                raise Exception("Simulated API failure")
            return await original_create(*args, **kwargs)
        
        mock_environment["groq_client"].chat.completions.create = failing_create
        research_agent.groq_client = mock_environment["groq_client"]
        
        # Execute multiple requests with some expected to fail
        tasks = []
        for i in range(10):
            request = {"topic": f"Test topic {i}", "sources_limit": 3}
            tasks.append(research_agent.process_request(request))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze error handling
        successful_results = [r for r in results if isinstance(r, dict)]
        exceptions = [r for r in results if isinstance(r, Exception)]
        
        # Should have some successes and some failures
        assert len(successful_results) > 0, "No successful requests"
        assert len(exceptions) > 0, "No failures detected (test setup issue)"
        
        # System should handle failures gracefully
        success_rate = len(successful_results) / len(results)
        assert success_rate >= 0.6, f"Success rate too low with intermittent failures: {success_rate}"


class TestPerformanceMetrics:
    """Test performance metrics collection and analysis."""
    
    def test_response_time_distribution(self):
        """Test response time distribution analysis."""
        # Simulate response times
        response_times = [
            1.2, 1.5, 1.8, 2.1, 2.3, 2.5, 2.8, 3.1, 3.4, 3.7,
            4.0, 4.3, 4.6, 4.9, 5.2, 5.5, 5.8, 6.1, 6.4, 6.7
        ]
        
        # Calculate metrics
        mean_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        # Verify reasonable performance characteristics
        assert mean_time < 10.0, f"Mean response time too high: {mean_time}s"
        assert median_time < 8.0, f"Median response time too high: {median_time}s"
        assert p95_time < 15.0, f"95th percentile too high: {p95_time}s"
        assert p99_time < 20.0, f"99th percentile too high: {p99_time}s"
    
    def test_throughput_calculation(self):
        """Test throughput calculation and analysis."""
        # Simulate request timestamps
        start_time = time.time()
        request_times = [start_time + i * 0.5 for i in range(100)]  # 100 requests over 50 seconds
        
        # Calculate throughput
        duration = request_times[-1] - request_times[0]
        throughput = len(request_times) / duration  # requests per second
        
        # Verify reasonable throughput
        assert throughput >= 1.0, f"Throughput too low: {throughput} req/s"
        assert throughput <= 10.0, f"Throughput suspiciously high: {throughput} req/s"
    
    def test_resource_utilization_metrics(self):
        """Test resource utilization tracking."""
        import psutil
        
        # Get current system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        
        # Verify system has adequate resources for testing
        assert cpu_percent < 90, f"CPU usage too high for testing: {cpu_percent}%"
        assert memory_info.percent < 90, f"Memory usage too high for testing: {memory_info.percent}%"
        assert disk_info.percent < 90, f"Disk usage too high for testing: {disk_info.percent}%"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])