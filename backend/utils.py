"""
Utility functions and helpers for the AI Website Navigator Backend
"""

import logging
import json
import time
from typing import Dict, Any, Optional, List
from functools import wraps
import asyncio
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests: int = 60, window_minutes: int = 1):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for client"""
        now = datetime.now()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Remove old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id] 
            if req_time > window_start
        ]
        
        # Check if under limit
        if len(self.requests[client_id]) < self.max_requests:
            self.requests[client_id].append(now)
            return True
        
        return False
    
    def get_reset_time(self, client_id: str) -> Optional[datetime]:
        """Get when the rate limit resets for a client"""
        if client_id not in self.requests or not self.requests[client_id]:
            return None
        
        oldest_request = min(self.requests[client_id])
        return oldest_request + timedelta(minutes=self.window_minutes)

class RequestCache:
    """Simple in-memory cache for API responses"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def _generate_key(self, request_data: Dict[str, Any]) -> str:
        """Generate cache key from request data"""
        # Create a deterministic hash of the request
        request_str = json.dumps(request_data, sort_keys=True)
        return hashlib.md5(request_str.encode()).hexdigest()
    
    def get(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired"""
        key = self._generate_key(request_data)
        
        if key in self.cache:
            cached_item = self.cache[key]
            if time.time() - cached_item["timestamp"] < self.ttl_seconds:
                logger.info(f"Cache hit for key: {key[:8]}...")
                return cached_item["data"]
            else:
                # Remove expired item
                del self.cache[key]
        
        return None
    
    def set(self, request_data: Dict[str, Any], response_data: Dict[str, Any]):
        """Cache a response"""
        key = self._generate_key(request_data)
        self.cache[key] = {
            "data": response_data,
            "timestamp": time.time()
        }
        logger.info(f"Cached response for key: {key[:8]}...")
    
    def clear(self):
        """Clear all cached items"""
        self.cache.clear()
        logger.info("Cleared cache")

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("ai_navigator.log")
        ]
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

def log_execution_time(func_name: str = None):
    """Decorator to log function execution time"""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            name = func_name or func.__name__
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"{name} completed in {execution_time:.2f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{name} failed after {execution_time:.2f}s: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            name = func_name or func.__name__
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"{name} completed in {execution_time:.2f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{name} failed after {execution_time:.2f}s: {e}")
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

def validate_dom_elements(dom_elements: List[Dict[str, Any]]) -> bool:
    """Validate DOM elements structure"""
    
    if not isinstance(dom_elements, list):
        return False
    
    required_fields = {"id", "tag", "text"}
    
    for element in dom_elements:
        if not isinstance(element, dict):
            return False
        
        if not required_fields.issubset(element.keys()):
            return False
        
        if not isinstance(element["id"], int):
            return False
        
        if not isinstance(element["tag"], str):
            return False
        
        if not isinstance(element["text"], str):
            return False
    
    return True

def sanitize_query(query: str) -> str:
    """Sanitize user query for processing"""
    
    if not isinstance(query, str):
        return ""
    
    # Basic sanitization
    sanitized = query.strip()
    sanitized = sanitized[:1000]  # Limit length
    
    # Remove potential harmful patterns
    harmful_patterns = ["<script", "javascript:", "data:", "vbscript:"]
    for pattern in harmful_patterns:
        sanitized = sanitized.replace(pattern, "")
    
    return sanitized

def extract_client_id(request) -> str:
    """Extract client identifier from request for rate limiting"""
    
    # Try to get IP address
    client_ip = getattr(request.client, 'host', 'unknown') if hasattr(request, 'client') else 'unknown'
    
    # In production, you might want to use other identifiers
    # like user ID, API key, etc.
    return client_ip

class HealthChecker:
    """Health check utilities"""
    
    @staticmethod
    async def check_openai_connection(api_key: str) -> bool:
        """Check if OpenAI API is accessible"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            
            # Make a simple test request
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False
    
    @staticmethod
    def check_embedding_model(model_name: str) -> bool:
        """Check if embedding model is accessible"""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(model_name)
            # Test encoding
            model.encode(["test"])
            return True
        except Exception as e:
            logger.error(f"Embedding model health check failed: {e}")
            return False
    
    @staticmethod
    def check_chroma_db(chroma_client=None) -> bool:
        """Check if ChromaDB is accessible"""
        try:
            if chroma_client is None:
                import chromadb
                from chromadb.config import Settings
                chroma_client = chromadb.PersistentClient(
                    path="./chroma_db",
                    settings=Settings(allow_reset=True)
                )
            
            # Try to get collections (lightweight operation)
            collections = chroma_client.list_collections()
            return True
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            return False

def format_error_response(error: Exception, include_details: bool = False) -> Dict[str, Any]:
    """Format error for API response"""
    
    error_response = {
        "error": type(error).__name__,
        "message": str(error)
    }
    
    if include_details:
        error_response["details"] = {
            "timestamp": datetime.now().isoformat(),
            "type": type(error).__name__
        }
    
    return error_response

def measure_similarity(text1: str, text2: str) -> float:
    """Simple text similarity measure"""
    
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 and not words2:
        return 1.0
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)

# Global instances
rate_limiter = RateLimiter()
request_cache = RequestCache()

# Initialize logging
setup_logging()
