"""
Comprehensive tests for API endpoints
"""

import pytest
import json
import time
from fastapi import status
from unittest.mock import patch, MagicMock

from models import ActionType, NavigatorResponse


class TestRootEndpoint:
    """Test the root endpoint /"""
    
    def test_root_endpoint_success(self, test_client):
        """Test successful root endpoint call"""
        response = test_client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["service"] == "AI Website Navigator"
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"
    
    def test_root_endpoint_response_format(self, test_client):
        """Test root endpoint response format"""
        response = test_client.get("/")
        data = response.json()
        
        required_fields = ["service", "version", "status", "docs"]
        for field in required_fields:
            assert field in data


class TestHealthEndpoint:
    """Test the health check endpoint /health"""
    
    def test_health_check_success(self, test_client):
        """Test successful health check"""
        response = test_client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data
        assert "ai_model" in data
    
    def test_health_check_response_structure(self, test_client):
        """Test health check response structure"""
        response = test_client.get("/health")
        data = response.json()
        
        required_fields = ["status", "version", "environment", "ai_model"]
        for field in required_fields:
            assert field in data
            assert data[field] is not None


class TestStatsEndpoint:
    """Test the stats endpoint /stats"""
    
    @patch('main.rag_system')
    def test_stats_endpoint_success(self, mock_rag_system, test_client):
        """Test successful stats retrieval"""
        # Mock RAG system responses
        mock_rag_system.patterns_collection.get.return_value = {"ids": ["p1", "p2", "p3"]}
        mock_rag_system.actions_collection.get.return_value = {"ids": ["a1", "a2"]}
        
        response = test_client.get("/stats")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "service" in data
        assert "cache_size" in data
        assert "patterns_count" in data
        assert "actions_count" in data
        assert data["patterns_count"] == 3
        assert data["actions_count"] == 2
    
    @patch('main.rag_system')
    def test_stats_endpoint_rag_error_handling(self, mock_rag_system, test_client):
        """Test stats endpoint when RAG system has errors"""
        # Mock RAG system to raise an exception
        mock_rag_system.patterns_collection.get.side_effect = Exception("DB Error")
        
        response = test_client.get("/stats")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should still return basic stats with 0 counts
        assert data["patterns_count"] == 0
        assert data["actions_count"] == 0


class TestPlanEndpoint:
    """Test the main /plan endpoint"""
    
    def test_plan_endpoint_success(self, test_client, sample_navigator_request, 
                                 mock_ai_engine, mock_rag_system, no_rate_limit, clear_cache):
        """Test successful plan request"""
        response = test_client.post("/plan", json=sample_navigator_request.model_dump())
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["action"] == "CLICK"
        assert data["elementId"] == 0
        assert "reasoning" in data
        assert "confidence" in data
    
    def test_plan_endpoint_empty_query(self, test_client, sample_navigator_request, 
                                      mock_ai_engine, mock_rag_system, no_rate_limit):
        """Test plan endpoint with empty query"""
        request_data = sample_navigator_request.model_dump()
        request_data["query"] = ""
        
        response = test_client.post("/plan", json=request_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        # Check for either "detail" or "message" field
        error_message = data.get("detail", data.get("message", "")).lower()
        assert "empty" in error_message
    
    def test_plan_endpoint_whitespace_query(self, test_client, sample_navigator_request, 
                                           mock_ai_engine, mock_rag_system, no_rate_limit):
        """Test plan endpoint with whitespace-only query"""
        request_data = sample_navigator_request.model_dump()
        request_data["query"] = "   \n\t   "
        
        response = test_client.post("/plan", json=request_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_plan_endpoint_empty_dom_snapshot(self, test_client, sample_navigator_request, 
                                             mock_ai_engine, mock_rag_system, no_rate_limit):
        """Test plan endpoint with empty DOM snapshot"""
        request_data = sample_navigator_request.model_dump()
        request_data["dom_snapshot"] = []
        
        response = test_client.post("/plan", json=request_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        # Check for either "detail" or "message" field
        error_message = data.get("detail", data.get("message", "")).lower()
        assert "empty" in error_message
    
    def test_plan_endpoint_invalid_dom_format(self, test_client, no_rate_limit):
        """Test plan endpoint with invalid DOM format"""
        invalid_request = {
            "query": "test query",
            "dom_snapshot": [{"invalid": "format"}],
            "history": []
        }
        
        response = test_client.post("/plan", json=invalid_request)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_plan_endpoint_missing_required_fields(self, test_client, no_rate_limit):
        """Test plan endpoint with missing required fields"""
        incomplete_request = {
            "query": "test query"
            # Missing dom_snapshot and history
        }
        
        response = test_client.post("/plan", json=incomplete_request)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_plan_endpoint_with_history(self, test_client, sample_navigator_request, 
                                      sample_actions, mock_ai_engine, mock_rag_system, 
                                      no_rate_limit, clear_cache):
        """Test plan endpoint with action history"""
        request_data = sample_navigator_request.model_dump()
        request_data["history"] = [action.model_dump() for action in sample_actions[:2]]
        
        response = test_client.post("/plan", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "action" in data
    
    def test_plan_endpoint_done_action(self, test_client, sample_navigator_request, 
                                     mock_rag_system, no_rate_limit, clear_cache):
        """Test plan endpoint returning DONE action"""
        with patch('main.ai_engine') as mock_engine:
            from unittest.mock import AsyncMock
            mock_response = NavigatorResponse(
                action=ActionType.DONE,
                summary="Task completed successfully",
                reasoning="All steps completed",
                confidence=1.0
            )
            mock_engine.decide_action = AsyncMock(return_value=mock_response)
            
            response = test_client.post("/plan", json=sample_navigator_request.model_dump())
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["action"] == "DONE"
            assert "summary" in data
    
    def test_plan_endpoint_type_action(self, test_client, sample_navigator_request, 
                                     mock_rag_system, no_rate_limit, clear_cache):
        """Test plan endpoint returning TYPE action"""
        with patch('main.ai_engine') as mock_engine:
            from unittest.mock import AsyncMock
            mock_response = NavigatorResponse(
                action=ActionType.TYPE,
                elementId=0,
                text="leather wallet",
                reasoning="Type search term",
                confidence=0.9
            )
            mock_engine.decide_action = AsyncMock(return_value=mock_response)
            
            response = test_client.post("/plan", json=sample_navigator_request.model_dump())
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["action"] == "TYPE"
            assert data["text"] == "leather wallet"
            assert data["elementId"] == 0
    
    def test_plan_endpoint_ai_engine_error(self, test_client, sample_navigator_request, 
                                         mock_rag_system, no_rate_limit, clear_cache):
        """Test plan endpoint when AI engine throws an error"""
        with patch('main.ai_engine') as mock_engine:
            mock_engine.decide_action.side_effect = Exception("AI Engine Error")
            
            response = test_client.post("/plan", json=sample_navigator_request.model_dump())
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_plan_endpoint_malicious_input_sanitization(self, test_client, sample_navigator_request, 
                                                       mock_ai_engine, mock_rag_system, 
                                                       no_rate_limit, clear_cache):
        """Test that malicious input is sanitized"""
        request_data = sample_navigator_request.model_dump()
        request_data["query"] = "search for <script>alert('xss')</script> wallet"
        
        response = test_client.post("/plan", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        # The sanitized query should be passed to the AI engine
        mock_ai_engine.decide_action.assert_called_once()
        call_args = mock_ai_engine.decide_action.call_args[0][0]
        assert "<script" not in call_args.query


class TestFeedbackEndpoint:
    """Test the feedback endpoint /feedback"""
    
    @patch('main.rag_system')
    def test_feedback_endpoint_success(self, mock_rag_system, test_client, 
                                     sample_dom_elements, sample_actions, no_rate_limit):
        """Test successful feedback submission"""
        feedback_data = {
            "query": "search for wallet",
            "success": True,
            "actions": [action.model_dump() for action in sample_actions],
            "dom_snapshot": [elem.model_dump() for elem in sample_dom_elements]
        }
        
        response = test_client.post("/feedback", json=feedback_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "feedback_recorded"
        assert "message" in data
        
        # Verify RAG system was called
        mock_rag_system.learn_from_interaction.assert_called_once()
    
    def test_feedback_endpoint_missing_query(self, test_client, no_rate_limit):
        """Test feedback endpoint with missing query"""
        feedback_data = {
            "success": True,
            "actions": [],
            "dom_snapshot": []
        }
        
        response = test_client.post("/feedback", json=feedback_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_feedback_endpoint_empty_query(self, test_client, no_rate_limit):
        """Test feedback endpoint with empty query"""
        feedback_data = {
            "query": "",
            "success": True,
            "actions": [],
            "dom_snapshot": []
        }
        
        response = test_client.post("/feedback", json=feedback_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_feedback_endpoint_without_dom_snapshot(self, test_client, no_rate_limit):
        """Test feedback endpoint without DOM snapshot"""
        feedback_data = {
            "query": "test query",
            "success": True,
            "actions": []
        }
        
        response = test_client.post("/feedback", json=feedback_data)
        
        assert response.status_code == status.HTTP_200_OK
        # Should still work but not call RAG learning
    
    @patch('main.rag_system')
    def test_feedback_endpoint_rag_error(self, mock_rag_system, test_client, 
                                       sample_dom_elements, no_rate_limit):
        """Test feedback endpoint when RAG system has error"""
        mock_rag_system.learn_from_interaction.side_effect = Exception("RAG Error")
        
        feedback_data = {
            "query": "test query",
            "success": True,
            "actions": [],
            "dom_snapshot": [elem.model_dump() for elem in sample_dom_elements]
        }
        
        response = test_client.post("/feedback", json=feedback_data)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limit_allows_normal_requests(self, test_client, sample_navigator_request):
        """Test that normal request rates are allowed"""
        with patch('utils.rate_limiter') as mock_limiter:
            mock_limiter.is_allowed.return_value = True
            
            response = test_client.post("/plan", json=sample_navigator_request.model_dump())
            
            # Should not be rate limited
            assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS
    
    def test_rate_limit_blocks_excessive_requests(self, test_client, sample_navigator_request):
        """Test that excessive requests are rate limited"""
        with patch('utils.rate_limiter') as mock_limiter:
            mock_limiter.is_allowed.return_value = False
            mock_limiter.get_reset_time.return_value = None
            
            response = test_client.post("/plan", json=sample_navigator_request.model_dump())
            
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            assert "Rate limit exceeded" in response.json()["detail"]
    
    def test_rate_limit_headers(self, test_client, sample_navigator_request):
        """Test rate limit response headers"""
        with patch('utils.rate_limiter') as mock_limiter:
            mock_limiter.is_allowed.return_value = False
            mock_limiter.get_reset_time.return_value = None
            
            response = test_client.post("/plan", json=sample_navigator_request.model_dump())
            
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            assert "Retry-After" in response.headers


class TestCaching:
    """Test caching functionality"""
    
    def test_cache_hit_returns_cached_response(self, test_client, sample_navigator_request, 
                                             mock_ai_engine, mock_rag_system, no_rate_limit):
        """Test that cache returns previously cached responses"""
        # Clear cache first
        from utils import request_cache
        request_cache.clear()
        
        # First request
        response1 = test_client.post("/plan", json=sample_navigator_request.model_dump())
        assert response1.status_code == status.HTTP_200_OK
        
        # Second identical request should hit cache
        response2 = test_client.post("/plan", json=sample_navigator_request.model_dump())
        assert response2.status_code == status.HTTP_200_OK
        
        # Should have same response
        assert response1.json() == response2.json()
    
    def test_cache_miss_with_different_query(self, test_client, sample_navigator_request, 
                                           mock_ai_engine, mock_rag_system, no_rate_limit, clear_cache):
        """Test that different queries don't hit cache"""
        # First request
        response1 = test_client.post("/plan", json=sample_navigator_request.model_dump())
        assert response1.status_code == status.HTTP_200_OK
        
        # Different query
        request_data = sample_navigator_request.model_dump()
        request_data["query"] = "different query"
        
        response2 = test_client.post("/plan", json=request_data)
        assert response2.status_code == status.HTTP_200_OK
        
        # AI engine should be called twice (no cache hit)
        assert mock_ai_engine.decide_action.call_count == 2


class TestErrorHandling:
    """Test error handling and exception scenarios"""
    
    def test_invalid_json_request(self, test_client, no_rate_limit):
        """Test handling of invalid JSON requests"""
        response = test_client.post("/plan", data="invalid json")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_request_validation_error_response_format(self, test_client, no_rate_limit):
        """Test validation error response format"""
        invalid_request = {
            "query": "test",
            "dom_snapshot": [{"invalid": "format"}]
        }
        
        response = test_client.post("/plan", json=invalid_request)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "error" in data
        assert "message" in data
    
    def test_internal_server_error_handling(self, test_client, sample_navigator_request, 
                                          mock_rag_system, no_rate_limit, clear_cache):
        """Test internal server error handling"""
        with patch('main.ai_engine') as mock_engine:
            mock_engine.decide_action.side_effect = Exception("Internal error")
            
            response = test_client.post("/plan", json=sample_navigator_request.model_dump())
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert "error" in data
            assert "message" in data


class TestClearCacheEndpoint:
    """Test the clear cache endpoint (development only)"""
    
    @patch('config.settings')
    def test_clear_cache_in_development(self, mock_settings, test_client):
        """Test cache clearing in development environment"""
        mock_settings.environment = "development"
        
        response = test_client.post("/clear-cache")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "cache_cleared"
    
    @patch('config.settings')
    def test_clear_cache_forbidden_in_production(self, mock_settings, test_client):
        """Test cache clearing is forbidden in production"""
        mock_settings.environment = "production"
        
        response = test_client.post("/clear-cache")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestResetRAGEndpoint:
    """Test the reset RAG endpoint (development only)"""
    
    @patch('config.settings')
    @patch('main.rag_system')
    def test_reset_rag_in_development(self, mock_rag_system, mock_settings, test_client):
        """Test RAG reset in development environment"""
        mock_settings.environment = "development"
        
        response = test_client.post("/reset-rag")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "rag_reset"
        mock_rag_system.reset_knowledge_base.assert_called_once()
    
    @patch('config.settings')
    def test_reset_rag_forbidden_in_production(self, mock_settings, test_client):
        """Test RAG reset is forbidden in production"""
        mock_settings.environment = "production"
        
        response = test_client.post("/reset-rag")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @patch('config.settings')
    @patch('main.rag_system')
    def test_reset_rag_error_handling(self, mock_rag_system, mock_settings, test_client):
        """Test RAG reset error handling"""
        mock_settings.environment = "development"
        mock_rag_system.reset_knowledge_base.side_effect = Exception("Reset error")
        
        response = test_client.post("/reset-rag")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
