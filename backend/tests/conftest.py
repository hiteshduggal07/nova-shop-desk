"""
Pytest configuration and fixtures for the AI Website Navigator Backend tests
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import os
import sys

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Set test environment variables BEFORE importing config
os.environ["ENVIRONMENT"] = "test" 
os.environ["OPENAI_API_KEY"] = "test_key_12345"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000,http://localhost:5173"
os.environ["CHROMA_PERSIST_DIRECTORY"] = tempfile.mkdtemp()
os.environ["LOG_LEVEL"] = "INFO"
os.environ["API_HOST"] = "0.0.0.0"
os.environ["API_PORT"] = "8000"

# Mock heavy dependencies if not available
try:
    import openai
except ImportError:
    import sys
    from unittest.mock import MagicMock
    sys.modules['openai'] = MagicMock()

try:
    import chromadb
except ImportError:
    import sys
    from unittest.mock import MagicMock
    sys.modules['chromadb'] = MagicMock()
    sys.modules['chromadb.config'] = MagicMock()

try:
    import sentence_transformers
except ImportError:
    import sys
    from unittest.mock import MagicMock
    sys.modules['sentence_transformers'] = MagicMock()

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

from models import DOMElement, Action, ActionType, NavigatorRequest, NavigatorResponse
from config import settings

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app"""
    from main import app
    return TestClient(app)

@pytest.fixture
def sample_dom_elements():
    """Sample DOM elements for testing"""
    return [
        DOMElement(id=0, tag="input", text="", type="search", placeholder="Search products..."),
        DOMElement(id=1, tag="button", text="Search"),
        DOMElement(id=2, tag="a", text="Home"),
        DOMElement(id=3, tag="a", text="Products"),
        DOMElement(id=4, tag="a", text="Cart (0)"),
        DOMElement(id=5, tag="button", text="Add to Cart"),
        DOMElement(id=6, tag="div", text="Leather Wallet - $29.99"),
        DOMElement(id=7, tag="button", text="Buy Now"),
        DOMElement(id=8, tag="input", text="", type="email", placeholder="Email address"),
        DOMElement(id=9, tag="button", text="Subscribe", type="submit")
    ]

@pytest.fixture
def sample_navigator_request(sample_dom_elements):
    """Sample NavigatorRequest for testing"""
    return NavigatorRequest(
        query="search for leather wallet",
        dom_snapshot=sample_dom_elements,
        history=[]
    )

@pytest.fixture
def sample_actions():
    """Sample actions for testing"""
    return [
        Action(action=ActionType.CLICK, elementId=0),
        Action(action=ActionType.TYPE, elementId=0, text="leather wallet"),
        Action(action=ActionType.CLICK, elementId=1),
        Action(action=ActionType.DONE, summary="Search completed successfully")
    ]

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    with patch('ai_engine.AsyncOpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock chat completions
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        yield mock_client

@pytest.fixture
def mock_rag_system():
    """Mock RAG system"""
    with patch('main.rag_system') as mock_rag:
        mock_rag.get_enhanced_context.return_value = MagicMock()
        mock_rag.learn_from_interaction = MagicMock()
        mock_rag.patterns_collection.get.return_value = {"ids": ["test1", "test2"]}
        mock_rag.actions_collection.get.return_value = {"ids": ["action1"]}
        yield mock_rag

@pytest.fixture
def mock_ai_engine():
    """Mock AI engine"""
    with patch('main.ai_engine') as mock_engine:
        mock_response = NavigatorResponse(
            action=ActionType.CLICK,
            elementId=0,
            reasoning="Test reasoning",
            confidence=0.9,
            text="",
            summary=""
        )
        mock_engine.decide_action = AsyncMock(return_value=mock_response)
        yield mock_engine

@pytest.fixture
def no_rate_limit():
    """Disable rate limiting for tests"""
    with patch('utils.rate_limiter') as mock_limiter:
        mock_limiter.is_allowed.return_value = True
        yield mock_limiter

@pytest.fixture
def clear_cache():
    """Clear request cache before each test"""
    from utils import request_cache
    request_cache.clear()
    yield
    request_cache.clear()

@pytest.fixture
def mock_sentence_transformer():
    """Mock sentence transformer for RAG tests"""
    with patch('rag_system.SentenceTransformer') as mock_transformer:
        mock_model = MagicMock()
        # Create a proper numpy-like array mock
        import numpy as np
        mock_embedding = np.array([[0.1, 0.2, 0.3]])
        mock_model.encode.return_value = mock_embedding
        mock_transformer.return_value = mock_model
        yield mock_model

@pytest.fixture
def mock_chromadb():
    """Mock ChromaDB for RAG tests"""
    with patch('rag_system.chromadb') as mock_chroma:
        mock_client = MagicMock()
        mock_collection = MagicMock()
        
        # Mock collection methods
        mock_collection.get.return_value = {"ids": []}
        mock_collection.add = MagicMock()
        mock_collection.query.return_value = {
            "documents": [["test document"]],
            "metadatas": [[{"context": "test", "confidence": 0.8}]],
            "distances": [[0.1]]
        }
        
        mock_client.get_collection.side_effect = Exception("Not found")
        mock_client.create_collection.return_value = mock_collection
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chroma.PersistentClient.return_value = mock_client
        
        yield mock_client

# Test data constants
TEST_QUERIES = [
    "search for leather wallet",
    "add this item to my cart", 
    "go to checkout",
    "navigate to home page",
    "find products under $50",
    "remove item from cart",
    "complete the purchase",
    "view product details",
    "apply discount code",
    "change quantity to 2"
]

TEST_INTENTS = [
    "SEARCH",
    "ADD_TO_CART", 
    "CHECKOUT",
    "NAVIGATE",
    "FILTER",
    "REMOVE_FROM_CART",
    "PURCHASE",
    "VIEW_PRODUCT",
    "APPLY_DISCOUNT",
    "CHANGE_QUANTITY"
]

# Performance test settings
STRESS_TEST_REQUESTS = 50
CONCURRENT_REQUESTS = 10
MAX_RESPONSE_TIME = 5.0  # seconds
