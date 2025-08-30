"""
Example FastAPI backend for the AI Website Navigator Agent
This is a template showing the expected API structure for the AI agent.

You'll need to implement the actual AI logic using GPT-4o-mini + RAG.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Website Navigator", version="1.0.0")

# Configure CORS for your React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DOMElement(BaseModel):
    id: int
    tag: str
    text: str
    type: Optional[str] = None
    placeholder: Optional[str] = None
    value: Optional[str] = None

class Action(BaseModel):
    action: str  # "CLICK", "TYPE", or "DONE"
    elementId: Optional[int] = None
    text: Optional[str] = None
    summary: Optional[str] = None

class NavigatorRequest(BaseModel):
    query: str
    dom_snapshot: List[DOMElement]
    history: List[Action]

class NavigatorResponse(BaseModel):
    action: str  # "CLICK", "TYPE", or "DONE"
    elementId: Optional[int] = None
    text: Optional[str] = None
    summary: Optional[str] = None

@app.post("/plan", response_model=NavigatorResponse)
async def plan_action(request: NavigatorRequest):
    """
    Main endpoint for the AI agent to request next actions.
    
    This is where you'll implement your GPT-4o-mini + RAG logic.
    """
    try:
        logger.info(f"Received query: {request.query}")
        logger.info(f"DOM elements: {len(request.dom_snapshot)}")
        logger.info(f"History length: {len(request.history)}")
        
        # TODO: Implement your AI logic here
        # 1. Process the user query
        # 2. Analyze the current DOM state
        # 3. Consider the action history
        # 4. Use RAG to understand the website structure
        # 5. Use GPT-4o-mini to decide the next action
        
        # Example logic (replace with your AI implementation):
        next_action = await decide_next_action(
            query=request.query,
            dom_elements=request.dom_snapshot,
            action_history=request.history
        )
        
        return next_action
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def decide_next_action(
    query: str, 
    dom_elements: List[DOMElement], 
    action_history: List[Action]
) -> NavigatorResponse:
    """
    This is where you'll implement your AI decision logic.
    
    Example implementation patterns:
    1. Parse the user intent from the query
    2. Map the intent to website actions
    3. Find relevant DOM elements for the action
    4. Return the appropriate action
    """
    
    # Example: Simple rule-based logic (replace with AI)
    query_lower = query.lower()
    
    # If this is the first action and user wants to search
    if not action_history and "search" in query_lower:
        # Find search input
        for element in dom_elements:
            if element.tag == "input" and (
                "search" in element.text.lower() or 
                element.type == "search" or
                "search" in (element.placeholder or "").lower()
            ):
                return NavigatorResponse(
                    action="CLICK",
                    elementId=element.id
                )
    
    # If we clicked a search input, now type the search term
    if (action_history and 
        action_history[-1].action == "CLICK" and 
        "search" in query_lower):
        
        # Extract search term from query
        # This is a simple example - you'd use NLP for this
        search_terms = ["leather", "wallet", "product"]
        search_term = None
        for term in search_terms:
            if term in query_lower:
                search_term = term
                break
        
        if search_term:
            # Find the search input that was clicked
            clicked_element_id = action_history[-1].elementId
            return NavigatorResponse(
                action="TYPE",
                elementId=clicked_element_id,
                text=search_term
            )
    
    # If we've typed in search, look for search button or submit
    if (len(action_history) >= 2 and 
        action_history[-1].action == "TYPE" and
        "search" in query_lower):
        
        # Find search button
        for element in dom_elements:
            if (element.tag == "button" and 
                ("search" in element.text.lower() or "submit" in element.text.lower())):
                return NavigatorResponse(
                    action="CLICK",
                    elementId=element.id
                )
    
    # Example: Add to cart logic
    if "add" in query_lower and "cart" in query_lower:
        for element in dom_elements:
            if (element.tag == "button" and 
                "add to cart" in element.text.lower()):
                return NavigatorResponse(
                    action="CLICK",
                    elementId=element.id
                )
    
    # Default: Mark as done if we can't find next action
    return NavigatorResponse(
        action="DONE",
        summary="Task completed or no further actions found."
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Website Navigator"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
To run this backend:

1. Install dependencies:
   pip install fastapi uvicorn

2. Run the server:
   uvicorn backend-example:app --reload --host 0.0.0.0 --port 8000

3. Test the endpoint:
   curl -X POST "http://localhost:8000/plan" \
   -H "Content-Type: application/json" \
   -d '{
     "query": "search for wallet",
     "dom_snapshot": [
       {"id": 0, "tag": "input", "text": "Search products", "type": "search"}
     ],
     "history": []
   }'

For production implementation:
1. Replace the example logic with GPT-4o-mini API calls
2. Implement RAG for website understanding
3. Add proper error handling and logging
4. Add authentication if needed
5. Optimize performance and add caching
6. Add rate limiting and security measures
"""
