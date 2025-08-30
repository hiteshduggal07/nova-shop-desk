"""
Performance and stress tests for the AI Website Navigator Backend
"""

import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock
import threading

from .conftest import STRESS_TEST_REQUESTS, CONCURRENT_REQUESTS, MAX_RESPONSE_TIME


class TestPerformance:
    """Test API performance under various conditions"""
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_single_request_response_time(self, mock_rag_system, mock_ai_engine, 
                                        test_client, sample_navigator_request, 
                                        no_rate_limit, clear_cache):
        """Test response time for a single request"""
        
        # Mock fast AI response
        mock_ai_engine.decide_action.return_value = MagicMock(
            action="CLICK",
            elementId=0,
            model_dump=lambda: {"action": "CLICK", "elementId": 0}
        )
        
        start_time = time.time()
        response = test_client.post("/plan", json=sample_navigator_request.model_dump())
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < MAX_RESPONSE_TIME
        print(f"Single request response time: {response_time:.3f}s")
    
    @patch('main.ai_engine')
    @patch('main.rag_system') 
    def test_cached_request_performance(self, mock_rag_system, mock_ai_engine,
                                      test_client, sample_navigator_request,
                                      no_rate_limit, clear_cache):
        """Test performance improvement with caching"""
        
        mock_ai_engine.decide_action.return_value = MagicMock(
            action="CLICK",
            elementId=0,
            model_dump=lambda: {"action": "CLICK", "elementId": 0}
        )
        
        request_data = sample_navigator_request.model_dump()
        
        # First request (cache miss)
        start_time = time.time()
        response1 = test_client.post("/plan", json=request_data)
        first_request_time = time.time() - start_time
        
        # Second identical request (cache hit)
        start_time = time.time()
        response2 = test_client.post("/plan", json=request_data)
        second_request_time = time.time() - start_time
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json() == response2.json()
        
        # Cache hit should be significantly faster
        print(f"First request (cache miss): {first_request_time:.3f}s")
        print(f"Second request (cache hit): {second_request_time:.3f}s")
        print(f"Performance improvement: {first_request_time / second_request_time:.1f}x")
        
        # Cache hit should be at least 2x faster for this simple case
        assert second_request_time < first_request_time / 2
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_sequential_requests_performance(self, mock_rag_system, mock_ai_engine,
                                           test_client, sample_navigator_request,
                                           no_rate_limit, clear_cache):
        """Test performance of sequential requests"""
        
        mock_ai_engine.decide_action.return_value = MagicMock(
            action="CLICK",
            elementId=0,
            model_dump=lambda: {"action": "CLICK", "elementId": 0}
        )
        
        num_requests = 10
        response_times = []
        
        for i in range(num_requests):
            # Vary the request slightly to avoid caching
            request_data = sample_navigator_request.model_dump()
            request_data["query"] = f"search for product {i}"
            
            start_time = time.time()
            response = test_client.post("/plan", json=request_data)
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        print(f"Sequential requests - Avg: {avg_response_time:.3f}s, "
              f"Max: {max_response_time:.3f}s, Min: {min_response_time:.3f}s")
        
        assert avg_response_time < MAX_RESPONSE_TIME
        assert max_response_time < MAX_RESPONSE_TIME * 2  # Allow some variance
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_concurrent_requests_performance(self, mock_rag_system, mock_ai_engine,
                                           test_client, sample_navigator_request,
                                           no_rate_limit, clear_cache):
        """Test performance under concurrent load"""
        
        mock_ai_engine.decide_action.return_value = MagicMock(
            action="CLICK",
            elementId=0,
            model_dump=lambda: {"action": "CLICK", "elementId": 0}
        )
        
        def make_request(request_id):
            request_data = sample_navigator_request.model_dump()
            request_data["query"] = f"concurrent request {request_id}"
            
            start_time = time.time()
            response = test_client.post("/plan", json=request_data)
            end_time = time.time()
            
            return {
                "request_id": request_id,
                "response_time": end_time - start_time,
                "status_code": response.status_code,
                "success": response.status_code == 200
            }
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
            futures = [executor.submit(make_request, i) for i in range(CONCURRENT_REQUESTS)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        response_times = [r["response_time"] for r in results]
        success_count = sum(1 for r in results if r["success"])
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        print(f"Concurrent requests ({CONCURRENT_REQUESTS}) - "
              f"Success: {success_count}/{CONCURRENT_REQUESTS}, "
              f"Avg: {avg_response_time:.3f}s, Max: {max_response_time:.3f}s")
        
        # All requests should succeed
        assert success_count == CONCURRENT_REQUESTS
        
        # Average response time should be reasonable
        assert avg_response_time < MAX_RESPONSE_TIME * 2  # Allow for concurrency overhead
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_large_dom_performance(self, mock_rag_system, mock_ai_engine,
                                 test_client, no_rate_limit, clear_cache):
        """Test performance with large DOM snapshots"""
        
        mock_ai_engine.decide_action.return_value = MagicMock(
            action="CLICK",
            elementId=0,
            model_dump=lambda: {"action": "CLICK", "elementId": 0}
        )
        
        # Create large DOM snapshot (100 elements)
        large_dom = []
        for i in range(100):
            large_dom.append({
                "id": i,
                "tag": "div" if i % 2 == 0 else "button",
                "text": f"Element {i} with some descriptive text content that makes it longer"
            })
        
        request_data = {
            "query": "test with large DOM",
            "dom_snapshot": large_dom,
            "history": []
        }
        
        start_time = time.time()
        response = test_client.post("/plan", json=request_data)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < MAX_RESPONSE_TIME * 2  # Allow extra time for large DOM
        
        print(f"Large DOM ({len(large_dom)} elements) response time: {response_time:.3f}s")
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_complex_history_performance(self, mock_rag_system, mock_ai_engine,
                                       test_client, sample_navigator_request,
                                       no_rate_limit, clear_cache):
        """Test performance with complex action history"""
        
        mock_ai_engine.decide_action.return_value = MagicMock(
            action="DONE",
            summary="Completed",
            model_dump=lambda: {"action": "DONE", "summary": "Completed"}
        )
        
        # Create complex history (20 actions)
        complex_history = []
        for i in range(20):
            if i % 3 == 0:
                complex_history.append({"action": "CLICK", "elementId": i % 5})
            elif i % 3 == 1:
                complex_history.append({"action": "TYPE", "elementId": i % 3, "text": f"text {i}"})
            else:
                complex_history.append({"action": "CLICK", "elementId": i % 7})
        
        request_data = sample_navigator_request.model_dump()
        request_data["history"] = complex_history
        
        start_time = time.time()
        response = test_client.post("/plan", json=request_data)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < MAX_RESPONSE_TIME * 1.5  # Allow some extra time
        
        print(f"Complex history ({len(complex_history)} actions) response time: {response_time:.3f}s")


class TestStressTesting:
    """Stress tests for high load scenarios"""
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_stress_test_plan_endpoint(self, mock_rag_system, mock_ai_engine,
                                     test_client, sample_navigator_request, clear_cache):
        """Stress test the /plan endpoint with many requests"""
        
        mock_ai_engine.decide_action.return_value = MagicMock(
            action="CLICK",
            elementId=0,
            model_dump=lambda: {"action": "CLICK", "elementId": 0}
        )
        
        # Disable rate limiting for stress test
        with patch('utils.rate_limiter') as mock_limiter:
            mock_limiter.is_allowed.return_value = True
            
            results = []
            start_time = time.time()
            
            for i in range(STRESS_TEST_REQUESTS):
                request_data = sample_navigator_request.model_dump()
                request_data["query"] = f"stress test request {i}"
                
                request_start = time.time()
                response = test_client.post("/plan", json=request_data)
                request_end = time.time()
                
                results.append({
                    "request_id": i,
                    "response_time": request_end - request_start,
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                })
            
            total_time = time.time() - start_time
        
        # Analyze results
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        response_times = [r["response_time"] for r in results if r["success"]]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
            requests_per_second = len(results) / total_time
        else:
            avg_response_time = float('inf')
            p95_response_time = float('inf')
            requests_per_second = 0
        
        print(f"Stress test results:")
        print(f"  Total requests: {len(results)}")
        print(f"  Success rate: {success_rate:.1%}")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  95th percentile response time: {p95_response_time:.3f}s")
        print(f"  Requests per second: {requests_per_second:.1f}")
        print(f"  Total time: {total_time:.3f}s")
        
        # Assertions
        assert success_rate >= 0.95  # At least 95% success rate
        assert avg_response_time < MAX_RESPONSE_TIME * 2  # Allow for stress overhead
        assert requests_per_second > 5  # Minimum throughput
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_memory_usage_under_load(self, mock_rag_system, mock_ai_engine,
                                   test_client, sample_navigator_request,
                                   no_rate_limit, clear_cache):
        """Test memory usage under sustained load"""
        
        mock_ai_engine.decide_action.return_value = MagicMock(
            action="CLICK",
            elementId=0,
            model_dump=lambda: {"action": "CLICK", "elementId": 0}
        )
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run sustained load
        num_requests = 20
        for i in range(num_requests):
            request_data = sample_navigator_request.model_dump()
            request_data["query"] = f"memory test request {i}"
            
            response = test_client.post("/plan", json=request_data)
            assert response.status_code == 200
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Memory usage:")
        print(f"  Initial: {initial_memory:.1f} MB")
        print(f"  Final: {final_memory:.1f} MB")
        print(f"  Increase: {memory_increase:.1f} MB")
        print(f"  Increase per request: {memory_increase / num_requests:.2f} MB")
        
        # Memory increase should be reasonable (less than 10MB per request)
        assert memory_increase / num_requests < 10
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_concurrent_stress_test(self, mock_rag_system, mock_ai_engine,
                                  test_client, sample_navigator_request, clear_cache):
        """Stress test with concurrent requests"""
        
        mock_ai_engine.decide_action.return_value = MagicMock(
            action="CLICK",
            elementId=0,
            model_dump=lambda: {"action": "CLICK", "elementId": 0}
        )
        
        # Disable rate limiting
        with patch('utils.rate_limiter') as mock_limiter:
            mock_limiter.is_allowed.return_value = True
            
            def concurrent_requests_batch(batch_id, requests_per_batch):
                batch_results = []
                for i in range(requests_per_batch):
                    request_data = sample_navigator_request.model_dump()
                    request_data["query"] = f"concurrent stress {batch_id}-{i}"
                    
                    start_time = time.time()
                    response = test_client.post("/plan", json=request_data)
                    end_time = time.time()
                    
                    batch_results.append({
                        "batch_id": batch_id,
                        "request_id": i,
                        "response_time": end_time - start_time,
                        "success": response.status_code == 200
                    })
                return batch_results
            
            # Run concurrent batches
            requests_per_batch = 10
            num_batches = 5
            
            with ThreadPoolExecutor(max_workers=num_batches) as executor:
                futures = [
                    executor.submit(concurrent_requests_batch, batch_id, requests_per_batch)
                    for batch_id in range(num_batches)
                ]
                
                all_results = []
                for future in as_completed(futures):
                    all_results.extend(future.result())
        
        # Analyze results
        total_requests = len(all_results)
        success_count = sum(1 for r in all_results if r["success"])
        success_rate = success_count / total_requests
        
        response_times = [r["response_time"] for r in all_results if r["success"]]
        avg_response_time = statistics.mean(response_times) if response_times else float('inf')
        
        print(f"Concurrent stress test:")
        print(f"  Batches: {num_batches}")
        print(f"  Requests per batch: {requests_per_batch}")
        print(f"  Total requests: {total_requests}")
        print(f"  Success rate: {success_rate:.1%}")
        print(f"  Average response time: {avg_response_time:.3f}s")
        
        # Assertions
        assert success_rate >= 0.9  # At least 90% success rate under stress
        assert avg_response_time < MAX_RESPONSE_TIME * 3  # Allow significant overhead


class TestScalabilityLimits:
    """Test scalability limits and breaking points"""
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_maximum_dom_size_limit(self, mock_rag_system, mock_ai_engine,
                                  test_client, no_rate_limit, clear_cache):
        """Test behavior with extremely large DOM snapshots"""
        
        mock_ai_engine.decide_action.return_value = MagicMock(
            action="DONE",
            summary="Handled large DOM",
            model_dump=lambda: {"action": "DONE", "summary": "Handled large DOM"}
        )
        
        # Test with increasingly large DOM sizes
        dom_sizes = [100, 500, 1000]
        
        for dom_size in dom_sizes:
            large_dom = []
            for i in range(dom_size):
                large_dom.append({
                    "id": i,
                    "tag": f"element-{i % 10}",
                    "text": f"Element {i} " * 5  # Make text longer
                })
            
            request_data = {
                "query": f"test with {dom_size} elements",
                "dom_snapshot": large_dom,
                "history": []
            }
            
            start_time = time.time()
            response = test_client.post("/plan", json=request_data)
            response_time = time.time() - start_time
            
            print(f"DOM size {dom_size}: {response_time:.3f}s, Status: {response.status_code}")
            
            # Should handle reasonable DOM sizes
            if dom_size <= 500:
                assert response.status_code == 200
                assert response_time < MAX_RESPONSE_TIME * 3
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_maximum_history_length_limit(self, mock_rag_system, mock_ai_engine,
                                        test_client, sample_navigator_request,
                                        no_rate_limit, clear_cache):
        """Test behavior with extremely long action histories"""
        
        mock_ai_engine.decide_action.return_value = MagicMock(
            action="DONE",
            summary="Handled long history",
            model_dump=lambda: {"action": "DONE", "summary": "Handled long history"}
        )
        
        # Test with increasingly long histories
        history_lengths = [10, 50, 100]
        
        for history_length in history_lengths:
            long_history = []
            for i in range(history_length):
                action_type = ["CLICK", "TYPE"][i % 2]
                if action_type == "CLICK":
                    long_history.append({"action": "CLICK", "elementId": i % 10})
                else:
                    long_history.append({"action": "TYPE", "elementId": i % 5, "text": f"text-{i}"})
            
            request_data = sample_navigator_request.model_dump()
            request_data["history"] = long_history
            
            start_time = time.time()
            response = test_client.post("/plan", json=request_data)
            response_time = time.time() - start_time
            
            print(f"History length {history_length}: {response_time:.3f}s, Status: {response.status_code}")
            
            # Should handle reasonable history lengths
            if history_length <= 50:
                assert response.status_code == 200
                assert response_time < MAX_RESPONSE_TIME * 2
    
    def test_rate_limit_effectiveness(self, test_client, sample_navigator_request):
        """Test that rate limiting effectively protects against overload"""
        
        # Use real rate limiter with low limits for testing
        with patch('config.settings') as mock_settings:
            mock_settings.max_requests_per_minute = 5  # Very low limit
            
            # Make requests until rate limited
            rate_limited_count = 0
            success_count = 0
            
            for i in range(10):
                request_data = sample_navigator_request.model_dump()
                request_data["query"] = f"rate limit test {i}"
                
                response = test_client.post("/plan", json=request_data)
                
                if response.status_code == 429:  # Too Many Requests
                    rate_limited_count += 1
                elif response.status_code == 200:
                    success_count += 1
            
            print(f"Rate limiting test: {success_count} successful, {rate_limited_count} rate limited")
            
            # Should have hit rate limit
            assert rate_limited_count > 0
            assert success_count <= 5  # Should respect the limit
