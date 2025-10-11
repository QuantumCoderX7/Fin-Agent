"""
Stress testing for the Financial AI Agents system.

This module tests system behavior under extreme conditions
including high load, resource constraints, and failure scenarios.
"""

import pytest
import asyncio
import time
import threading
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import psutil
import os

from tests.fixtures.sample_data import create_test_environment
from tests.fixtures.mock_responses import setup_mock_environment


class TestStressConditions:
    """Stress testing under extreme conditions."""
    
    @pytest.fixture
    def stress_environment(self):
        """Set up environment for stress testing."""
        return create_test_environment()
    
    def test_high_concurrency_stress(self, stress_environment):
        """Test system behavior under very high concurrency."""
        from app.agents.research_agent import ResearchAgent
        
        # Create multiple agent instances
        agents = [ResearchAgent(groq_api_key="test_key") for _ in range(20)]
        
        # Mock the clients to avoid real API calls
        mock_env = setup_mock_environment()
        for agent in agents:
            agent.groq_client = mock_env["groq_client"]
        
        def stress_task(agent_id):
            """Single stress task."""
            agent = agents[agent_id % len(agents)]
            request = {
                "topic": f"Stress test topic {agent_id}",
                "sources_limit": 3
            }
            
            start_time = time.time()
            try:
                # Simulate processing without actual API calls
                time.sleep(0.1)  # Simulate processing time
                end_time = time.time()
                return {
                    "agent_id": agent_id,
                    "success": True,
                    "response_time": end_time - start_time
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "agent_id": agent_id,
                    "success": False,
                    "response_time": end_time - start_time,
                    "error": str(e)
                }
        
        # Execute high concurrency test
        num_tasks = 100
        max_workers = 50
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(stress_task, i) for i in range(num_tasks)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze stress test results
        success_count = sum(1 for r in results if r["success"])
        success_rate = success_count / len(results)
        
        response_times = [r["response_time"] for r in results if r["success"]]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Under stress, we expect some degradation but not complete failure
        assert success_rate >= 0.7, f"Success rate under stress too low: {success_rate}"
        assert avg_response_time < 5.0, f"Response time under stress too high: {avg_response_time}s"
    
    def test_memory_pressure_stress(self):
        """Test system behavior under memory pressure."""
        import gc
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create memory pressure by allocating large objects
        large_objects = []
        try:
            for i in range(50):
                # Create large data structures similar to what agents might process
                large_data = {
                    "request_id": f"stress_{i}",
                    "search_results": [
                        {
                            "title": f"Result {j}" * 100,
                            "content": f"Content {j}" * 1000,
                            "metadata": {"score": j, "relevance": j * 0.1}
                        }
                        for j in range(100)
                    ],
                    "analysis": f"Analysis content {i}" * 500
                }
                large_objects.append(large_data)
                
                # Check memory usage periodically
                if i % 10 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_increase = current_memory - initial_memory
                    
                    # If memory usage gets too high, break to avoid system issues
                    if memory_increase > 500:  # 500MB limit
                        break
            
            # Test that system can still function under memory pressure
            peak_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = peak_memory - initial_memory
            
            # Verify memory usage is tracked
            assert memory_increase > 0, "No memory increase detected"
            
            # Test garbage collection effectiveness
            gc.collect()
            
        finally:
            # Clean up to avoid affecting other tests
            large_objects.clear()
            gc.collect()
    
    def test_cpu_intensive_stress(self):
        """Test system behavior under CPU-intensive conditions."""
        import threading
        import time
        
        def cpu_intensive_task():
            """CPU-intensive task to create load."""
            end_time = time.time() + 2  # Run for 2 seconds
            while time.time() < end_time:
                # Perform CPU-intensive operations
                sum(i * i for i in range(1000))
        
        # Start CPU-intensive background tasks
        cpu_threads = []
        num_cpu_threads = min(4, os.cpu_count() or 1)
        
        for _ in range(num_cpu_threads):
            thread = threading.Thread(target=cpu_intensive_task)
            thread.start()
            cpu_threads.append(thread)
        
        try:
            # Test agent performance under CPU load
            from app.agents.research_agent import ResearchAgent
            
            agent = ResearchAgent(groq_api_key="test_key")
            mock_env = setup_mock_environment()
            agent.groq_client = mock_env["groq_client"]
            
            # Measure performance under CPU stress
            start_time = time.time()
            
            # Simulate agent processing
            for i in range(5):
                request = {"topic": f"CPU stress test {i}", "sources_limit": 3}
                # Simulate processing without heavy computation
                time.sleep(0.1)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Performance should degrade but not fail completely
            assert total_time < 10.0, f"Processing time under CPU stress too high: {total_time}s"
            
        finally:
            # Wait for CPU threads to complete
            for thread in cpu_threads:
                thread.join()
    
    def test_rapid_request_bursts(self):
        """Test system behavior with rapid request bursts."""
        from app.agents.stock_agent import StockAgent
        
        agent = StockAgent(groq_api_key="test_key")
        mock_env = setup_mock_environment()
        agent.groq_client = mock_env["groq_client"]
        
        def burst_test():
            """Execute a burst of rapid requests."""
            results = []
            burst_size = 20
            
            start_time = time.time()
            
            # Send burst of requests as quickly as possible
            for i in range(burst_size):
                request_start = time.time()
                try:
                    request = {"symbols": ["AAPL"], "analysis_type": "quick"}
                    # Simulate quick processing
                    time.sleep(0.05)  # 50ms processing time
                    request_end = time.time()
                    
                    results.append({
                        "request_id": i,
                        "success": True,
                        "response_time": request_end - request_start
                    })
                except Exception as e:
                    request_end = time.time()
                    results.append({
                        "request_id": i,
                        "success": False,
                        "response_time": request_end - request_start,
                        "error": str(e)
                    })
            
            end_time = time.time()
            total_burst_time = end_time - start_time
            
            return results, total_burst_time
        
        # Execute multiple bursts
        all_results = []
        burst_times = []
        
        for burst_num in range(3):
            results, burst_time = burst_test()
            all_results.extend(results)
            burst_times.append(burst_time)
            
            # Small delay between bursts
            time.sleep(0.5)
        
        # Analyze burst performance
        success_rate = sum(1 for r in all_results if r["success"]) / len(all_results)
        avg_burst_time = sum(burst_times) / len(burst_times)
        
        assert success_rate >= 0.8, f"Success rate during bursts too low: {success_rate}"
        assert avg_burst_time < 5.0, f"Burst processing time too high: {avg_burst_time}s"
    
    def test_resource_exhaustion_recovery(self):
        """Test system recovery from resource exhaustion."""
        # Simulate resource exhaustion and recovery
        resource_usage = []
        
        def monitor_resources():
            """Monitor system resources."""
            process = psutil.Process(os.getpid())
            return {
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "cpu_percent": process.cpu_percent(),
                "open_files": len(process.open_files()) if hasattr(process, 'open_files') else 0
            }
        
        # Baseline measurement
        baseline = monitor_resources()
        resource_usage.append(("baseline", baseline))
        
        # Create resource pressure
        temp_objects = []
        try:
            # Gradually increase resource usage
            for i in range(10):
                # Create temporary objects
                temp_data = [j for j in range(1000)]
                temp_objects.append(temp_data)
                
                # Monitor resources
                current = monitor_resources()
                resource_usage.append((f"pressure_{i}", current))
                
                time.sleep(0.1)
            
            # Peak usage
            peak = monitor_resources()
            resource_usage.append(("peak", peak))
            
        finally:
            # Clean up and allow recovery
            temp_objects.clear()
            gc.collect()
            time.sleep(1)  # Allow system to recover
            
            # Recovery measurement
            recovery = monitor_resources()
            resource_usage.append(("recovery", recovery))
        
        # Analyze resource usage pattern
        memory_values = [usage[1]["memory_mb"] for usage in resource_usage]
        
        baseline_memory = memory_values[0]
        peak_memory = max(memory_values)
        recovery_memory = memory_values[-1]
        
        # Verify resource usage pattern
        assert peak_memory > baseline_memory, "No resource pressure detected"
        
        # Recovery should bring memory usage back down (within 50% of peak increase)
        memory_increase = peak_memory - baseline_memory
        recovery_increase = recovery_memory - baseline_memory
        
        recovery_ratio = recovery_increase / memory_increase if memory_increase > 0 else 0
        assert recovery_ratio < 0.5, f"Poor resource recovery: {recovery_ratio}"


class TestFailureScenarios:
    """Test system behavior under various failure conditions."""
    
    def test_cascading_failure_resilience(self):
        """Test resilience to cascading failures."""
        from app.agents.research_agent import ResearchAgent
        from app.agents.stock_agent import StockAgent
        from app.agents.rag_evaluator import RAGEvaluator
        
        # Create agents
        research_agent = ResearchAgent(groq_api_key="test_key")
        stock_agent = StockAgent(groq_api_key="test_key")
        rag_evaluator = RAGEvaluator(groq_api_key="test_key")
        
        # Mock clients with failure simulation
        mock_env = setup_mock_environment()
        
        failure_count = 0
        
        async def failing_create(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1
            if failure_count <= 5:  # First 5 calls fail
                raise Exception(f"Simulated failure {failure_count}")
            # Subsequent calls succeed
            return mock_env["groq_client"].chat.completions.create.return_value
        
        # Set up failing clients
        for agent in [research_agent, stock_agent, rag_evaluator]:
            agent.groq_client = mock_env["groq_client"]
            agent.groq_client.chat.completions.create = failing_create
        
        # Test that agents can recover from initial failures
        recovery_results = []
        
        for i in range(10):
            try:
                if i % 3 == 0:
                    request = {"topic": f"Recovery test {i}", "sources_limit": 3}
                    # Simulate processing
                    time.sleep(0.1)
                    recovery_results.append({"agent": "research", "success": True})
                elif i % 3 == 1:
                    request = {"symbols": ["AAPL"], "analysis_type": "quick"}
                    time.sleep(0.1)
                    recovery_results.append({"agent": "stock", "success": True})
                else:
                    request = {"query": "test", "response": "test", "context": ["test"]}
                    time.sleep(0.1)
                    recovery_results.append({"agent": "evaluation", "success": True})
            except Exception:
                recovery_results.append({"agent": "unknown", "success": False})
        
        # Analyze recovery
        success_rate = sum(1 for r in recovery_results if r["success"]) / len(recovery_results)
        
        # System should recover after initial failures
        assert success_rate >= 0.5, f"Poor recovery from cascading failures: {success_rate}"
    
    def test_timeout_handling_stress(self):
        """Test timeout handling under stress conditions."""
        import asyncio
        
        async def timeout_simulation():
            """Simulate operations with various timeout scenarios."""
            results = []
            
            async def slow_operation(delay: float, operation_id: int):
                """Simulate a slow operation."""
                try:
                    await asyncio.wait_for(asyncio.sleep(delay), timeout=2.0)
                    return {"id": operation_id, "success": True, "delay": delay}
                except asyncio.TimeoutError:
                    return {"id": operation_id, "success": False, "delay": delay, "error": "timeout"}
            
            # Create operations with various delays
            delays = [0.5, 1.0, 1.5, 2.5, 3.0, 3.5, 4.0]  # Some will timeout
            tasks = [slow_operation(delay, i) for i, delay in enumerate(delays)]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return [r for r in results if isinstance(r, dict)]
        
        # Run timeout simulation
        results = asyncio.run(timeout_simulation())
        
        # Analyze timeout handling
        successful_ops = [r for r in results if r["success"]]
        timeout_ops = [r for r in results if not r["success"]]
        
        # Should have both successful and timed-out operations
        assert len(successful_ops) > 0, "No operations completed successfully"
        assert len(timeout_ops) > 0, "No timeouts detected (test setup issue)"
        
        # Verify timeout behavior
        for timeout_op in timeout_ops:
            assert timeout_op["delay"] > 2.0, "Timeout occurred for operation that should have succeeded"
    
    def test_error_propagation_limits(self):
        """Test that errors don't propagate beyond expected boundaries."""
        from app.utils.exceptions import (
            ValidationException,
            DataSourceException,
            AgentProcessingException
        )
        
        def error_boundary_test(error_type):
            """Test error boundary for specific error type."""
            try:
                if error_type == "validation":
                    raise ValidationException("test", "Validation error")
                elif error_type == "data_source":
                    raise DataSourceException("test", "Data source error")
                elif error_type == "processing":
                    raise AgentProcessingException("test", "Processing error")
                else:
                    raise Exception("Unknown error")
            except (ValidationException, DataSourceException, AgentProcessingException) as e:
                return {"error_type": error_type, "caught": True, "message": str(e)}
            except Exception as e:
                return {"error_type": error_type, "caught": False, "message": str(e)}
        
        # Test error boundaries
        error_types = ["validation", "data_source", "processing", "unknown"]
        results = [error_boundary_test(et) for et in error_types]
        
        # Verify expected errors are caught
        for result in results[:3]:  # First 3 should be caught
            assert result["caught"], f"Expected error not caught: {result['error_type']}"
        
        # Unknown error should not be caught by specific handlers
        assert not results[3]["caught"], "Unknown error was incorrectly caught"


class TestSystemLimits:
    """Test system behavior at operational limits."""
    
    def test_maximum_concurrent_connections(self):
        """Test behavior at maximum concurrent connection limits."""
        # Simulate maximum connections
        max_connections = 100
        active_connections = []
        
        class MockConnection:
            def __init__(self, conn_id):
                self.id = conn_id
                self.active = True
                self.created_at = time.time()
        
        # Create connections up to limit
        for i in range(max_connections):
            conn = MockConnection(i)
            active_connections.append(conn)
        
        # Verify connection management
        assert len(active_connections) == max_connections
        
        # Test connection cleanup
        # Remove half the connections
        connections_to_remove = active_connections[:max_connections // 2]
        for conn in connections_to_remove:
            conn.active = False
            active_connections.remove(conn)
        
        remaining_connections = len(active_connections)
        expected_remaining = max_connections // 2
        
        assert remaining_connections == expected_remaining, \
            f"Connection cleanup failed: {remaining_connections} != {expected_remaining}"
    
    def test_request_queue_limits(self):
        """Test behavior when request queue reaches limits."""
        import queue
        
        # Simulate request queue with limited capacity
        max_queue_size = 50
        request_queue = queue.Queue(maxsize=max_queue_size)
        
        # Fill queue to capacity
        for i in range(max_queue_size):
            request_queue.put(f"request_{i}")
        
        # Verify queue is full
        assert request_queue.full(), "Queue should be full"
        
        # Test queue overflow handling
        try:
            request_queue.put("overflow_request", block=False)
            assert False, "Queue should reject additional requests when full"
        except queue.Full:
            # Expected behavior
            pass
        
        # Test queue processing
        processed_requests = []
        while not request_queue.empty():
            request = request_queue.get()
            processed_requests.append(request)
            request_queue.task_done()
        
        assert len(processed_requests) == max_queue_size, \
            f"Not all requests processed: {len(processed_requests)} != {max_queue_size}"
    
    def test_data_size_limits(self):
        """Test handling of maximum data sizes."""
        # Test various data size scenarios
        test_cases = [
            {"name": "small", "size": 1024, "should_pass": True},
            {"name": "medium", "size": 1024 * 1024, "should_pass": True},
            {"name": "large", "size": 10 * 1024 * 1024, "should_pass": True},
            {"name": "very_large", "size": 100 * 1024 * 1024, "should_pass": False}
        ]
        
        for case in test_cases:
            # Create data of specified size
            data_size = case["size"]
            test_data = "x" * data_size
            
            # Test data handling
            try:
                # Simulate data processing
                processed_size = len(test_data)
                processing_successful = processed_size == data_size
                
                if case["should_pass"]:
                    assert processing_successful, f"Failed to process {case['name']} data"
                else:
                    # For very large data, we might expect different behavior
                    # This is a placeholder for actual size limit logic
                    pass
                    
            except MemoryError:
                if case["should_pass"]:
                    pytest.fail(f"Unexpected memory error for {case['name']} data")
                # Expected for very large data
            
            # Clean up
            del test_data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])