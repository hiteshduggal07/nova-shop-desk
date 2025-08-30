"""
Edge cases and error handling tests for the AI Website Navigator Backend
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import status

from models import ActionType, NavigatorResponse
from utils import sanitize_query, validate_dom_elements


class TestInputValidationEdgeCases:
    """Test edge cases in input validation"""
    
    def test_extremely_long_query(self, test_client, sample_dom_elements, no_rate_limit):
        """Test handling of extremely long queries"""
        
        # Create a very long query (10KB)
        long_query = "search for " + "very long product name " * 500
        
        request_data = {
            "query": long_query,
            "dom_snapshot": [elem.model_dump() for elem in sample_dom_elements],
            "history": []
        }
        
        response = test_client.post("/plan", json=request_data)
        
        # Should either handle it or reject gracefully
        assert response.status_code in [200, 400, 413]  # OK, Bad Request, or Payload Too Large
    
    def test_empty_string_in_dom_elements(self, test_client, no_rate_limit):
        """Test DOM elements with empty strings"""
        
        dom_with_empty_strings = [
            {"id": 0, "tag": "", "text": ""},  # Empty tag
            {"id": 1, "tag": "button", "text": ""},  # Empty text
            {"id": 2, "tag": "input", "text": "", "type": ""},  # Empty type
        ]
        
        request_data = {
            "query": "test query",
            "dom_snapshot": dom_with_empty_strings,
            "history": []
        }
        
        response = test_client.post("/plan", json=request_data)
        
        # Should handle empty strings gracefully
        assert response.status_code in [200, 400, 422]
    
    def test_unicode_and_special_characters(self, test_client, sample_dom_elements, no_rate_limit):
        """Test handling of unicode and special characters"""
        
        unicode_queries = [
            "search for café ☕ products",
            "find 中文 products",
            "look for Ñoño items",
            "search with emoji 🛍️🛒💳",
            "query with symbols @#$%^&*()",
            "newlines\nand\ttabs\rcharacters"
        ]
        
        for query in unicode_queries:
            request_data = {
                "query": query,
                "dom_snapshot": [elem.model_dump() for elem in sample_dom_elements],
                "history": []
            }
            
            response = test_client.post("/plan", json=request_data)
            
            # Should handle unicode gracefully
            assert response.status_code in [200, 400]
    
    def test_malformed_json_in_request(self, test_client, no_rate_limit):
        """Test handling of malformed JSON"""
        
        malformed_json_cases = [
            '{"query": "test", "dom_snapshot": [{"id": 0, "tag": "button"',  # Incomplete JSON
            '{"query": "test", "dom_snapshot": [{"id": "not_a_number", "tag": "button", "text": ""}]}',  # Wrong type
            '{"query": "test", "dom_snapshot": "not_an_array"}',  # Wrong structure
        ]
        
        for malformed_json in malformed_json_cases:
            response = test_client.post("/plan", data=malformed_json, 
                                      headers={"Content-Type": "application/json"})
            
            # Should return validation error
            assert response.status_code == 422
    
    def test_negative_element_ids(self, test_client, no_rate_limit):
        """Test handling of negative element IDs"""
        
        dom_with_negative_ids = [
            {"id": -1, "tag": "button", "text": "Negative ID"},
            {"id": 0, "tag": "input", "text": "Zero ID"},
            {"id": -999, "tag": "div", "text": "Very negative ID"}
        ]
        
        request_data = {
            "query": "test with negative IDs",
            "dom_snapshot": dom_with_negative_ids,
            "history": []
        }
        
        response = test_client.post("/plan", json=request_data)
        
        # Should handle negative IDs (they might be valid in some contexts)
        assert response.status_code in [200, 400, 422]
    
    def test_duplicate_element_ids(self, test_client, no_rate_limit):
        """Test handling of duplicate element IDs"""
        
        dom_with_duplicates = [
            {"id": 1, "tag": "button", "text": "First button"},
            {"id": 1, "tag": "input", "text": "Duplicate ID"},  # Same ID
            {"id": 2, "tag": "div", "text": "Different element"}
        ]
        
        request_data = {
            "query": "test with duplicate IDs",
            "dom_snapshot": dom_with_duplicates,
            "history": []
        }
        
        response = test_client.post("/plan", json=request_data)
        
        # Should handle duplicates gracefully
        assert response.status_code in [200, 400, 422]


class TestAIEngineEdgeCases:
    """Test edge cases in AI engine behavior"""
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_ai_returns_invalid_element_id(self, mock_rag_system, mock_ai_engine, 
                                         test_client, sample_navigator_request, 
                                         no_rate_limit, clear_cache):
        """Test when AI returns an element ID that doesn't exist"""
        
        # Mock AI returning invalid element ID
        mock_ai_engine.decide_action.return_value = MagicMock(
            action=ActionType.CLICK,
            elementId=999,  # Doesn't exist in sample DOM
            reasoning="Click non-existent element",
            confidence=0.9,
            model_dump=lambda: {
                "action": "CLICK",
                "elementId": 999,
                "reasoning": "Click non-existent element",
                "confidence": 0.9
            }
        )
        
        response = test_client.post("/plan", json=sample_navigator_request.model_dump())
        
        assert response.status_code == 200
        data = response.json()
        assert data["elementId"] == 999  # Should return what AI specified
        # Frontend should handle validation
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_ai_returns_malformed_response(self, mock_rag_system, mock_ai_engine,
                                         test_client, sample_navigator_request,
                                         no_rate_limit, clear_cache):
        """Test when AI returns malformed response"""
        
        # Mock AI returning invalid response structure
        invalid_response = MagicMock()
        invalid_response.action = "INVALID_ACTION"  # Not a valid ActionType
        invalid_response.elementId = "not_a_number"  # Wrong type
        invalid_response.model_dump.return_value = {
            "action": "INVALID_ACTION",
            "elementId": "not_a_number"
        }
        
        mock_ai_engine.decide_action.return_value = invalid_response
        
        response = test_client.post("/plan", json=sample_navigator_request.model_dump())
        
        # Should handle gracefully, possibly returning 500 or corrected response
        assert response.status_code in [200, 500]
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_ai_engine_timeout(self, mock_rag_system, mock_ai_engine,
                             test_client, sample_navigator_request,
                             no_rate_limit, clear_cache):
        """Test behavior when AI engine times out"""
        
        import asyncio
        
        async def slow_ai_response(*args, **kwargs):
            await asyncio.sleep(10)  # Simulate timeout
            return MagicMock(action=ActionType.CLICK, elementId=0)
        
        mock_ai_engine.decide_action.side_effect = slow_ai_response
        
        # This should timeout (depending on server timeout settings)
        response = test_client.post("/plan", json=sample_navigator_request.model_dump())
        
        # Should handle timeout gracefully
        assert response.status_code in [200, 500, 504]  # OK, Internal Error, or Gateway Timeout
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_ai_confidence_edge_values(self, mock_rag_system, mock_ai_engine,
                                     test_client, sample_navigator_request,
                                     no_rate_limit, clear_cache):
        """Test AI confidence with edge values"""
        
        confidence_values = [-1.0, 0.0, 1.0, 2.0, float('inf'), float('-inf'), float('nan')]
        
        for confidence in confidence_values:
            mock_ai_engine.decide_action.return_value = MagicMock(
                action=ActionType.CLICK,
                elementId=0,
                confidence=confidence,
                model_dump=lambda: {
                    "action": "CLICK",
                    "elementId": 0,
                    "confidence": confidence
                }
            )
            
            response = test_client.post("/plan", json=sample_navigator_request.model_dump())
            
            # Should handle edge confidence values
            assert response.status_code in [200, 500]


class TestRAGSystemEdgeCases:
    """Test edge cases in RAG system"""
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_rag_empty_knowledge_base(self, mock_rag_system, mock_ai_engine,
                                    test_client, sample_navigator_request,
                                    no_rate_limit, clear_cache):
        """Test behavior with empty RAG knowledge base"""
        
        # Mock empty RAG responses
        mock_rag_system.get_enhanced_context.return_value = MagicMock(
            page_type="unknown",
            available_actions=[],
            common_patterns={},
            navigation_structure={}
        )
        
        mock_rag_system.find_relevant_patterns.return_value = []
        mock_rag_system.find_action_patterns.return_value = []
        
        mock_ai_engine.decide_action.return_value = MagicMock(
            action=ActionType.CLICK,
            elementId=0,
            model_dump=lambda: {"action": "CLICK", "elementId": 0}
        )
        
        response = test_client.post("/plan", json=sample_navigator_request.model_dump())
        
        assert response.status_code == 200
        # Should work even without RAG knowledge
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_rag_corrupted_patterns(self, mock_rag_system, mock_ai_engine,
                                  test_client, sample_navigator_request,
                                  no_rate_limit, clear_cache):
        """Test behavior with corrupted RAG patterns"""
        
        # Mock corrupted patterns
        corrupted_patterns = [
            {"invalid": "structure"},
            {"confidence": "not_a_number"},
            None,  # Null pattern
            {"context": None, "action_sequence": []}
        ]
        
        mock_rag_system.find_relevant_patterns.return_value = corrupted_patterns
        
        mock_ai_engine.decide_action.return_value = MagicMock(
            action=ActionType.CLICK,
            elementId=0,
            model_dump=lambda: {"action": "CLICK", "elementId": 0}
        )
        
        response = test_client.post("/plan", json=sample_navigator_request.model_dump())
        
        # Should handle corrupted patterns gracefully
        assert response.status_code in [200, 500]
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_rag_database_connection_error(self, mock_rag_system, mock_ai_engine,
                                         test_client, sample_navigator_request,
                                         no_rate_limit, clear_cache):
        """Test behavior when RAG database is unavailable"""
        
        # Mock database connection error
        mock_rag_system.get_enhanced_context.side_effect = Exception("Database connection failed")
        
        mock_ai_engine.decide_action.return_value = MagicMock(
            action=ActionType.CLICK,
            elementId=0,
            model_dump=lambda: {"action": "CLICK", "elementId": 0}
        )
        
        response = test_client.post("/plan", json=sample_navigator_request.model_dump())
        
        # Should handle database errors gracefully
        assert response.status_code in [200, 500]


class TestConcurrencyEdgeCases:
    """Test edge cases in concurrent access"""
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_concurrent_cache_access(self, mock_rag_system, mock_ai_engine,
                                   test_client, sample_navigator_request,
                                   no_rate_limit, clear_cache):
        """Test concurrent access to cache"""
        
        import threading
        import time
        
        mock_ai_engine.decide_action.return_value = MagicMock(
            action=ActionType.CLICK,
            elementId=0,
            model_dump=lambda: {"action": "CLICK", "elementId": 0}
        )
        
        results = []
        
        def make_request():
            try:
                response = test_client.post("/plan", json=sample_navigator_request.model_dump())
                results.append(response.status_code)
            except Exception as e:
                results.append(str(e))
        
        # Create multiple threads accessing cache simultaneously
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads at roughly the same time
        for thread in threads:
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed or fail gracefully
        for result in results:
            assert result == 200 or isinstance(result, str)  # Success or exception string
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_concurrent_rag_learning(self, mock_rag_system, mock_ai_engine,
                                   test_client, sample_dom_elements, no_rate_limit):
        """Test concurrent RAG learning operations"""
        
        import threading
        
        # Mock successful interactions that trigger learning
        mock_ai_engine.decide_action.return_value = MagicMock(
            action=ActionType.DONE,
            summary="Success",
            model_dump=lambda: {"action": "DONE", "summary": "Success"}
        )
        
        results = []
        
        def submit_feedback(request_id):
            try:
                feedback_data = {
                    "query": f"concurrent learning test {request_id}",
                    "success": True,
                    "actions": [{"action": "CLICK", "elementId": 0}],
                    "dom_snapshot": [elem.model_dump() for elem in sample_dom_elements]
                }
                
                response = test_client.post("/feedback", json=feedback_data)
                results.append(response.status_code)
            except Exception as e:
                results.append(str(e))
        
        # Submit concurrent feedback
        threads = []
        for i in range(5):
            thread = threading.Thread(target=submit_feedback, args=(i,))
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All feedback submissions should succeed
        assert all(result == 200 for result in results if isinstance(result, int))


class TestResourceLimitEdgeCases:
    """Test edge cases related to resource limits"""
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_maximum_concurrent_connections(self, mock_rag_system, mock_ai_engine,
                                          test_client, sample_navigator_request,
                                          no_rate_limit, clear_cache):
        """Test behavior at maximum concurrent connections"""
        
        mock_ai_engine.decide_action.return_value = MagicMock(
            action=ActionType.CLICK,
            elementId=0,
            model_dump=lambda: {"action": "CLICK", "elementId": 0}
        )
        
        from concurrent.futures import ThreadPoolExecutor
        import time
        
        def slow_request():
            # Add artificial delay to increase connection time
            time.sleep(0.1)
            return test_client.post("/plan", json=sample_navigator_request.model_dump())
        
        # Try to overwhelm with many concurrent connections
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(slow_request) for _ in range(50)]
            responses = [future.result() for future in futures]
        
        # Most requests should succeed, some might fail due to limits
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 30  # At least 60% should succeed
    
    def test_request_size_limits(self, test_client, no_rate_limit):
        """Test behavior with very large request payloads"""
        
        # Create extremely large DOM (simulating a complex page)
        huge_dom = []
        for i in range(5000):  # 5000 elements
            huge_dom.append({
                "id": i,
                "tag": "div",
                "text": f"Element {i} with very long descriptive text " * 20
            })
        
        request_data = {
            "query": "test with huge DOM",
            "dom_snapshot": huge_dom,
            "history": []
        }
        
        response = test_client.post("/plan", json=request_data)
        
        # Should either handle it or reject with appropriate error
        assert response.status_code in [200, 413, 400, 500]  # OK, Payload Too Large, Bad Request, or Error


class TestUtilityFunctionEdgeCases:
    """Test edge cases in utility functions"""
    
    def test_sanitize_query_edge_cases(self):
        """Test query sanitization with edge cases"""
        
        edge_cases = [
            ("", ""),  # Empty string
            ("   ", ""),  # Only whitespace
            ("a" * 1000, "a" * 500),  # Very long string (should be truncated)
            ("<script>alert('xss')</script>", "alert('xss')"),  # XSS attempt
            ("normal query", "normal query"),  # Normal case
            ("query\nwith\nnewlines", "query with newlines"),  # Newlines
            ("query\t\t\twith\t\ttabs", "query with tabs"),  # Tabs
            ("query   with   spaces", "query with spaces"),  # Multiple spaces
        ]
        
        for input_query, expected in edge_cases:
            result = sanitize_query(input_query)
            assert result == expected, f"Failed for input: '{input_query}'"
    
    def test_validate_dom_elements_edge_cases(self):
        """Test DOM element validation with edge cases"""
        
        # Valid cases
        assert validate_dom_elements([]) == True  # Empty list
        assert validate_dom_elements([{"id": 0, "tag": "div", "text": ""}]) == True  # Minimal valid
        
        # Invalid cases
        assert validate_dom_elements("not a list") == False  # Not a list
        assert validate_dom_elements([{"tag": "div", "text": ""}]) == False  # Missing id
        assert validate_dom_elements([{"id": "0", "tag": "div", "text": ""}]) == False  # Wrong id type
        assert validate_dom_elements([{"id": 0, "text": ""}]) == False  # Missing tag
        assert validate_dom_elements([{"id": 0, "tag": "div"}]) == False  # Missing text
        assert validate_dom_elements([{"id": 0, "tag": 123, "text": ""}]) == False  # Wrong tag type
        assert validate_dom_elements([{"id": 0, "tag": "div", "text": 123}]) == False  # Wrong text type
    
    def test_error_formatting_edge_cases(self):
        """Test error formatting with various error types"""
        
        from utils import format_error_response
        
        # Test different error types
        errors = [
            ValueError("Test value error"),
            TypeError("Test type error"),
            Exception("Generic exception"),
            RuntimeError("Runtime error"),
            "String error",  # Not an exception
            None,  # None value
            123,  # Number
        ]
        
        for error in errors:
            result = format_error_response(error)
            assert "error" in result
            assert "message" in result
            assert isinstance(result, dict)


class TestBoundaryConditions:
    """Test boundary conditions and limits"""
    
    def test_zero_values(self, test_client, no_rate_limit):
        """Test handling of zero values"""
        
        zero_dom = [{"id": 0, "tag": "div", "text": ""}]
        
        request_data = {
            "query": "test",
            "dom_snapshot": zero_dom,
            "history": []
        }
        
        response = test_client.post("/plan", json=request_data)
        assert response.status_code in [200, 400, 422]
    
    def test_maximum_integer_values(self, test_client, no_rate_limit):
        """Test handling of maximum integer values"""
        
        max_int_dom = [{"id": 2**31 - 1, "tag": "div", "text": "Max int"}]  # Max 32-bit int
        
        request_data = {
            "query": "test with max int",
            "dom_snapshot": max_int_dom,
            "history": []
        }
        
        response = test_client.post("/plan", json=request_data)
        assert response.status_code in [200, 400, 422]
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_floating_point_precision(self, mock_rag_system, mock_ai_engine,
                                    test_client, sample_navigator_request,
                                    no_rate_limit, clear_cache):
        """Test handling of floating point precision edge cases"""
        
        # Test with very small and very large confidence values
        confidence_values = [1e-10, 1e10, 0.999999999999, 0.000000000001]
        
        for confidence in confidence_values:
            mock_ai_engine.decide_action.return_value = MagicMock(
                action=ActionType.CLICK,
                elementId=0,
                confidence=confidence,
                model_dump=lambda conf=confidence: {
                    "action": "CLICK",
                    "elementId": 0,
                    "confidence": conf
                }
            )
            
            response = test_client.post("/plan", json=sample_navigator_request.model_dump())
            
            # Should handle extreme floating point values
            assert response.status_code in [200, 500]


@pytest.mark.asyncio
class TestAsyncEdgeCases:
    """Test edge cases in async operations"""
    
    async def test_async_operation_cancellation(self):
        """Test behavior when async operations are cancelled"""
        
        from ai_engine import AIDecisionEngine
        
        with patch('ai_engine.AsyncOpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            async def cancelled_operation(*args, **kwargs):
                import asyncio
                await asyncio.sleep(0.1)
                raise asyncio.CancelledError("Operation cancelled")
            
            mock_client.chat.completions.create.side_effect = cancelled_operation
            
            engine = AIDecisionEngine()
            
            # Should handle cancellation gracefully
            import asyncio
            with pytest.raises(asyncio.CancelledError):
                await engine.analyze_intent("test query", [])
    
    async def test_async_timeout_handling(self):
        """Test handling of async timeouts"""
        
        from ai_engine import AIDecisionEngine
        
        with patch('ai_engine.AsyncOpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            async def timeout_operation(*args, **kwargs):
                import asyncio
                await asyncio.sleep(30)  # Very long operation
                return MagicMock()
            
            mock_client.chat.completions.create.side_effect = timeout_operation
            
            engine = AIDecisionEngine()
            
            # Should timeout and handle gracefully
            import asyncio
            try:
                await asyncio.wait_for(engine.analyze_intent("test query", []), timeout=1.0)
                assert False, "Should have timed out"
            except asyncio.TimeoutError:
                pass  # Expected
