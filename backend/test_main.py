"""
Tests for the AI Website Navigator Backend
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

# Import the app
from main import app
from models import DOMElement, Action, ActionType, NavigatorRequest
from config import settings

# Override settings for testing
settings.environment = "test"
settings.openai_api_key = "test_key"

client = TestClient(app)

# Test data
sample_dom_elements = [
    DOMElement(id=0, tag="input", text="Search products", type="search"),
    DOMElement(id=1, tag="button", text="Search"),
    DOMElement(id=2, tag="button", text="Add to Cart"),
    DOMElement(id=3, tag="a", text="Home"),
    DOMElement(id=4, tag="a", text="Products")
]

sample_request = NavigatorRequest(
    query="search for leather wallet",
    dom_snapshot=sample_dom_elements,
    history=[]
)

class TestBasicEndpoints:
    """Test basic API endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "AI Website Navigator"
        assert "version" in data
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data
    
    def test_stats_endpoint(self):
        """Test stats endpoint"""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "cache_size" in data

class TestPlanEndpoint:
    """Test the main /plan endpoint"""
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_plan_success(self, mock_rag_system, mock_ai_engine):
        """Test successful plan request"""
        # Mock RAG system
        mock_context = MagicMock()
        mock_rag_system.get_enhanced_context.return_value = mock_context
        
        # Mock AI engine
        mock_response = MagicMock()
        mock_response.action = ActionType.CLICK
        mock_response.elementId = 0
        mock_response.text = None
        mock_response.summary = None
        mock_response.reasoning = "Click on search input"
        mock_response.confidence = 0.9
        mock_response.model_dump.return_value = {
            "action": "CLICK",
            "elementId": 0,
            "text": None,
            "summary": None,
            "reasoning": "Click on search input",
            "confidence": 0.9
        }
        
        mock_ai_engine.decide_action = AsyncMock(return_value=mock_response)
        
        # Make request
        response = client.post("/plan", json=sample_request.model_dump())
        
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "CLICK"
        assert data["elementId"] == 0
    
    def test_plan_empty_query(self):
        """Test plan with empty query"""
        invalid_request = sample_request.model_copy()
        invalid_request.query = ""
        
        response = client.post("/plan", json=invalid_request.model_dump())
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()
    
    def test_plan_empty_dom(self):
        """Test plan with empty DOM snapshot"""
        invalid_request = sample_request.model_copy()
        invalid_request.dom_snapshot = []
        
        response = client.post("/plan", json=invalid_request.model_dump())
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()
    
    def test_plan_invalid_dom_format(self):
        """Test plan with invalid DOM format"""
        invalid_data = sample_request.model_dump()
        invalid_data["dom_snapshot"] = [{"invalid": "format"}]
        
        response = client.post("/plan", json=invalid_data)
        assert response.status_code == 422  # Validation error

class TestFeedbackEndpoint:
    """Test the /feedback endpoint"""
    
    @patch('main.rag_system')
    def test_feedback_success(self, mock_rag_system):
        """Test successful feedback submission"""
        feedback_data = {
            "query": "search for wallet",
            "success": True,
            "actions": [{"action": "CLICK", "elementId": 0}],
            "dom_snapshot": [elem.model_dump() for elem in sample_dom_elements]
        }
        
        response = client.post("/feedback", json=feedback_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "feedback_recorded"
    
    def test_feedback_missing_query(self):
        """Test feedback with missing query"""
        feedback_data = {
            "success": True,
            "actions": []
        }
        
        response = client.post("/feedback", json=feedback_data)
        assert response.status_code == 400

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    @patch('main.rate_limiter')
    def test_rate_limit_exceeded(self, mock_rate_limiter):
        """Test rate limit exceeded"""
        mock_rate_limiter.is_allowed.return_value = False
        mock_rate_limiter.get_reset_time.return_value = None
        
        response = client.post("/plan", json=sample_request.model_dump())
        assert response.status_code == 429

class TestValidationUtils:
    """Test validation utilities"""
    
    def test_validate_dom_elements_valid(self):
        """Test DOM element validation with valid data"""
        from utils import validate_dom_elements
        
        valid_elements = [
            {"id": 0, "tag": "button", "text": "Click me"},
            {"id": 1, "tag": "input", "text": "", "type": "text"}
        ]
        
        assert validate_dom_elements(valid_elements) == True
    
    def test_validate_dom_elements_invalid(self):
        """Test DOM element validation with invalid data"""
        from utils import validate_dom_elements
        
        invalid_elements = [
            {"tag": "button", "text": "Click me"},  # Missing id
            {"id": "not_int", "tag": "input", "text": ""}  # Invalid id type
        ]
        
        assert validate_dom_elements(invalid_elements) == False
    
    def test_sanitize_query(self):
        """Test query sanitization"""
        from utils import sanitize_query
        
        # Test normal query
        assert sanitize_query("search for wallet") == "search for wallet"
        
        # Test malicious query
        malicious = "search <script>alert('xss')</script>"
        sanitized = sanitize_query(malicious)
        assert "<script" not in sanitized
        
        # Test empty query
        assert sanitize_query("   ") == ""

class TestAIEngine:
    """Test AI engine functionality"""
    
    @pytest.mark.asyncio
    async def test_intent_analysis(self):
        """Test intent analysis"""
        from ai_engine import AIDecisionEngine
        
        with patch('ai_engine.AsyncOpenAI') as mock_openai:
            # Mock OpenAI response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "primary_intent": "SEARCH",
                "entities": ["leather", "wallet"],
                "required_steps": ["click_search", "type_query", "submit_search"],
                "confidence": 0.9
            })
            
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client
            
            engine = AIDecisionEngine()
            intent = await engine.analyze_intent("search for leather wallet", [])
            
            assert intent.primary_intent == "SEARCH"
            assert "leather" in intent.entities
            assert intent.confidence == 0.9

class TestRAGSystem:
    """Test RAG system functionality"""
    
    def test_rag_initialization(self):
        """Test RAG system initialization"""
        from rag_system import WebsiteRAGSystem
        
        with patch('rag_system.chromadb.PersistentClient') as mock_client:
            with patch('rag_system.SentenceTransformer') as mock_transformer:
                mock_collection = MagicMock()
                mock_collection.get.return_value = {"ids": []}
                
                mock_chroma = MagicMock()
                mock_chroma.get_collection.side_effect = Exception("Not found")
                mock_chroma.create_collection.return_value = mock_collection
                mock_client.return_value = mock_chroma
                
                rag_system = WebsiteRAGSystem()
                assert rag_system is not None
    
    def test_dom_description(self):
        """Test DOM state description"""
        from rag_system import WebsiteRAGSystem
        
        with patch('rag_system.chromadb.PersistentClient'):
            with patch('rag_system.SentenceTransformer'):
                rag_system = WebsiteRAGSystem()
                description = rag_system._describe_dom_state(sample_dom_elements[:3])
                
                assert "input" in description
                assert "button" in description
                assert "Search" in description

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
