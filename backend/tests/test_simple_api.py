"""
Simplified API tests without heavy dependencies
"""

import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

# Set test environment
os.environ["OPENAI_API_KEY"] = "test_key_for_testing"
os.environ["ENVIRONMENT"] = "test"

def test_basic_imports():
    """Test that we can import basic modules"""
    from models import DOMElement, Action, ActionType
    
    element = DOMElement(id=0, tag="button", text="Test")
    assert element.id == 0
    
    action = Action(action=ActionType.CLICK, elementId=0)
    assert action.action == ActionType.CLICK

@patch('main.rag_system')
@patch('main.ai_engine')
def test_health_endpoint(mock_ai_engine, mock_rag_system):
    """Test the health endpoint"""
    from main import app
    client = TestClient(app)
    
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "environment" in data

@patch('main.rag_system')
@patch('main.ai_engine')
def test_root_endpoint(mock_ai_engine, mock_rag_system):
    """Test the root endpoint"""
    from main import app
    client = TestClient(app)
    
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "service" in data
    assert data["service"] == "AI Website Navigator"

@patch('main.rag_system')
@patch('main.ai_engine')
def test_stats_endpoint(mock_ai_engine, mock_rag_system):
    """Test the stats endpoint"""
    # Mock RAG system stats
    mock_rag_system.patterns_collection.get.return_value = {"ids": ["test1", "test2"]}
    mock_rag_system.actions_collection.get.return_value = {"ids": ["action1"]}
    
    from main import app
    client = TestClient(app)
    
    response = client.get("/stats")
    assert response.status_code == 200
    
    data = response.json()
    assert "service" in data
    assert "patterns_count" in data
    assert "actions_count" in data

@patch('utils.rate_limiter')
@patch('main.rag_system')
@patch('main.ai_engine')
def test_plan_endpoint_basic(mock_ai_engine, mock_rag_system, mock_rate_limiter):
    """Test the plan endpoint with basic request"""
    # Mock rate limiter
    mock_rate_limiter.is_allowed.return_value = True
    
    # Mock RAG system
    mock_rag_system.get_enhanced_context.return_value = MagicMock()
    mock_rag_system.learn_from_interaction = MagicMock()
    
    # Mock AI engine
    mock_response = MagicMock()
    mock_response.action = "CLICK"
    mock_response.elementId = 0
    mock_response.text = None
    mock_response.summary = None
    mock_response.reasoning = "Test reasoning"
    mock_response.confidence = 0.9
    mock_response.model_dump.return_value = {
        "action": "CLICK",
        "elementId": 0,
        "text": None,
        "summary": None,
        "reasoning": "Test reasoning", 
        "confidence": 0.9
    }
    mock_ai_engine.decide_action = AsyncMock(return_value=mock_response)
    
    from main import app
    client = TestClient(app)
    
    # Test data
    request_data = {
        "query": "test search",
        "dom_snapshot": [
            {"id": 0, "tag": "input", "text": "Search", "type": "search"},
            {"id": 1, "tag": "button", "text": "Submit"}
        ],
        "history": []
    }
    
    response = client.post("/plan", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["action"] == "CLICK"
    assert data["elementId"] == 0

@patch('utils.rate_limiter')
@patch('main.rag_system')
def test_plan_endpoint_validation_errors(mock_rag_system, mock_rate_limiter):
    """Test plan endpoint input validation"""
    mock_rate_limiter.is_allowed.return_value = True
    
    from main import app
    client = TestClient(app)
    
    # Test empty query
    request_data = {
        "query": "",
        "dom_snapshot": [{"id": 0, "tag": "button", "text": "Test"}],
        "history": []
    }
    
    response = client.post("/plan", json=request_data)
    assert response.status_code == 400
    
    # Test empty DOM snapshot
    request_data = {
        "query": "test query",
        "dom_snapshot": [],
        "history": []
    }
    
    response = client.post("/plan", json=request_data)
    assert response.status_code == 400

@patch('utils.rate_limiter')
@patch('main.rag_system')
def test_feedback_endpoint(mock_rag_system, mock_rate_limiter):
    """Test the feedback endpoint"""
    mock_rate_limiter.is_allowed.return_value = True
    
    from main import app
    client = TestClient(app)
    
    feedback_data = {
        "query": "test query",
        "success": True,
        "actions": [{"action": "CLICK", "elementId": 0}],
        "dom_snapshot": [{"id": 0, "tag": "button", "text": "Test"}]
    }
    
    response = client.post("/feedback", json=feedback_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "feedback_recorded"

def test_rate_limiting():
    """Test rate limiting functionality"""
    with patch('utils.rate_limiter') as mock_limiter:
        mock_limiter.is_allowed.return_value = False
        mock_limiter.get_reset_time.return_value = None
        
        from main import app
        client = TestClient(app)
        
        request_data = {
            "query": "test",
            "dom_snapshot": [{"id": 0, "tag": "button", "text": "Test"}],
            "history": []
        }
        
        response = client.post("/plan", json=request_data)
        assert response.status_code == 429  # Too Many Requests

@patch('main.rag_system')
@patch('main.ai_engine')
def test_malformed_request(mock_ai_engine, mock_rag_system):
    """Test handling of malformed requests"""
    from main import app
    client = TestClient(app)
    
    # Send invalid JSON
    response = client.post("/plan", data="invalid json")
    assert response.status_code == 422  # Validation error
