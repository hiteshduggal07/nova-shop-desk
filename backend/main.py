"""
FastAPI Main Application for AI Website Navigator
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from models import (
    NavigatorRequest, NavigatorResponse, HealthResponse, ErrorResponse,
    ActionType
)
from ai_engine import AIDecisionEngine
from rag_system import WebsiteRAGSystem
from config import settings
from utils import (
    rate_limiter, request_cache, extract_client_id, validate_dom_elements,
    sanitize_query, log_execution_time, format_error_response, HealthChecker
)

logger = logging.getLogger(__name__)

# Global instances
ai_engine: AIDecisionEngine = None
rag_system: WebsiteRAGSystem = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global ai_engine, rag_system
    
    logger.info("Starting AI Website Navigator Backend...")
    
    try:
        # Initialize AI engine
        ai_engine = AIDecisionEngine()
        logger.info("✓ AI Engine initialized")
        
        # Initialize RAG system
        rag_system = WebsiteRAGSystem()
        logger.info("✓ RAG System initialized")
        
        # Health checks
        if settings.environment != "test":
            openai_ok = await HealthChecker.check_openai_connection(settings.openai_api_key)
            embedding_ok = HealthChecker.check_embedding_model(settings.embedding_model)
            chroma_ok = HealthChecker.check_chroma_db(chroma_client=rag_system.chroma_client)
            
            logger.info(f"Health checks - OpenAI: {openai_ok}, Embeddings: {embedding_ok}, ChromaDB: {chroma_ok}")
        
        logger.info("🚀 Backend startup complete")
        
    except Exception as e:
        logger.error(f"Failed to initialize backend: {e}")
        raise
    
    yield
    
    logger.info("Shutting down AI Website Navigator Backend...")

# Create FastAPI app
app = FastAPI(
    title="AI Website Navigator",
    description="Backend service for AI-powered website navigation",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()
    
    # Log request
    logger.info(f"📨 {request.method} {request.url.path} from {request.client.host}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"📤 {response.status_code} in {process_time:.2f}s")
    
    return response

# Rate limiting dependency
async def check_rate_limit(request: Request):
    """Check rate limit for request"""
    client_id = extract_client_id(request)
    
    if not rate_limiter.is_allowed(client_id):
        reset_time = rate_limiter.get_reset_time(client_id)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Reset at {reset_time}",
            headers={"Retry-After": "60"}
        )

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(exc, include_details=settings.environment == "development")
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    return JSONResponse(
        status_code=422,
        content={
            "error": "ValidationError",
            "message": "Invalid request format",
            "details": exc.errors() if settings.environment == "development" else None
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=format_error_response(
            exc, 
            include_details=settings.environment == "development"
        )
    )

# Routes
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "service": "AI Website Navigator",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment=settings.environment,
        ai_model=settings.openai_model
    )

@app.post("/plan", response_model=NavigatorResponse)
@log_execution_time("plan_action")
async def plan_action(
    request: NavigatorRequest,
    http_request: Request,
    _: None = Depends(check_rate_limit)
):
    """
    Main endpoint for AI navigation planning
    
    This endpoint receives the current state of the webpage and user query,
    then returns the next action the AI agent should take.
    """
    
    try:
        # Validate request
        if not request.query.strip():
            raise HTTPException(
                status_code=400, 
                detail="Query cannot be empty"
            )
        
        if not request.dom_snapshot:
            raise HTTPException(
                status_code=400,
                detail="DOM snapshot cannot be empty"
            )
        
        # Sanitize query
        request.query = sanitize_query(request.query)
        
        # Validate DOM elements
        dom_dict = [elem.model_dump() for elem in request.dom_snapshot]
        if not validate_dom_elements(dom_dict):
            raise HTTPException(
                status_code=400,
                detail="Invalid DOM elements format"
            )
        
        # Check cache first
        cache_key = {
            "query": request.query,
            "dom_elements": len(request.dom_snapshot),
            "history_length": len(request.history)
        }
        
        cached_response = request_cache.get(cache_key)
        if cached_response:
            logger.info("Returning cached response")
            return NavigatorResponse(**cached_response)
        
        # Process with AI
        logger.info(f"Processing query: '{request.query}' with {len(request.dom_snapshot)} DOM elements")
        
        # Get enhanced context from RAG system
        website_context = rag_system.get_enhanced_context(request.query, request.dom_snapshot)
        
        # Enhanced AI engine with RAG context
        ai_engine.website_context = website_context
        
        # Get AI decision
        response = await ai_engine.decide_action(request)
        
        # Cache successful responses
        if response.action != ActionType.DONE or response.summary:
            request_cache.set(cache_key, response.model_dump())
        
        # Learn from the interaction for future improvements
        if len(request.history) > 0:
            # Determine if the sequence was successful
            success = response.action == ActionType.DONE and "error" not in (response.summary or "").lower()
            
            if success:
                rag_system.learn_from_interaction(
                    query=request.query,
                    dom_elements=request.dom_snapshot,
                    actions_taken=[action.model_dump() for action in request.history],
                    success=True
                )
        
        logger.info(f"Returning action: {response.action}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in plan_action: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/feedback")
async def submit_feedback(
    request: Dict[str, Any],
    _: None = Depends(check_rate_limit)
):
    """
    Submit feedback about AI actions for learning
    
    This endpoint allows the frontend to report whether an action sequence
    was successful or not, helping the AI learn and improve.
    """
    
    try:
        query = request.get("query", "")
        success = request.get("success", False)
        actions = request.get("actions", [])
        dom_snapshot = request.get("dom_snapshot", [])
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Learn from feedback
        if dom_snapshot:
            from models import DOMElement
            dom_elements = [DOMElement(**elem) for elem in dom_snapshot]
            
            rag_system.learn_from_interaction(
                query=query,
                dom_elements=dom_elements,
                actions_taken=actions,
                success=success
            )
        
        logger.info(f"Received feedback: query='{query}', success={success}, actions={len(actions)}")
        
        return {"status": "feedback_recorded", "message": "Thank you for your feedback"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to process feedback")

@app.get("/stats")
async def get_stats():
    """Get service statistics"""
    
    try:
        # Get cache stats
        cache_size = len(request_cache.cache)
        
        # Get RAG stats
        patterns_count = 0
        actions_count = 0
        
        try:
            patterns_result = rag_system.patterns_collection.get()
            patterns_count = len(patterns_result["ids"])
            
            actions_result = rag_system.actions_collection.get()
            actions_count = len(actions_result["ids"])
        except Exception:
            pass
        
        return {
            "service": "AI Website Navigator",
            "cache_size": cache_size,
            "patterns_count": patterns_count,
            "actions_count": actions_count,
            "ai_model": settings.openai_model,
            "environment": settings.environment
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@app.post("/clear-cache")
async def clear_cache():
    """Clear the request cache (for debugging)"""
    
    if settings.environment == "production":
        raise HTTPException(status_code=403, detail="Not allowed in production")
    
    request_cache.clear()
    return {"status": "cache_cleared"}

@app.post("/reset-rag")
async def reset_rag():
    """Reset the RAG knowledge base (for debugging)"""
    
    if settings.environment == "production":
        raise HTTPException(status_code=403, detail="Not allowed in production")
    
    try:
        rag_system.reset_knowledge_base()
        return {"status": "rag_reset"}
    except Exception as e:
        logger.error(f"Error resetting RAG: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset RAG system")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
