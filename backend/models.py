"""
Pydantic models for the AI Website Navigator API
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class ActionType(str, Enum):
    """Supported action types"""
    CLICK = "CLICK"
    TYPE = "TYPE"
    DONE = "DONE"

class DOMElement(BaseModel):
    """Represents a DOM element from the frontend"""
    id: int = Field(..., description="Unique identifier for the element")
    tag: str = Field(..., description="HTML tag name (e.g., 'button', 'input')")
    text: str = Field(..., description="Visible text content of the element")
    type: Optional[str] = Field(None, description="Input type if applicable")
    placeholder: Optional[str] = Field(None, description="Placeholder text if applicable")
    value: Optional[str] = Field(None, description="Current value if applicable")

class Action(BaseModel):
    """Represents an action taken by the agent"""
    action: ActionType = Field(..., description="Type of action to perform")
    elementId: Optional[int] = Field(None, description="ID of target element")
    text: Optional[str] = Field(None, description="Text to type (for TYPE actions)")
    summary: Optional[str] = Field(None, description="Summary of completion (for DONE actions)")

class NavigatorRequest(BaseModel):
    """Request payload for the /plan endpoint"""
    query: str = Field(..., description="User's natural language command")
    dom_snapshot: List[DOMElement] = Field(..., description="Current DOM state")
    history: List[Action] = Field(default_factory=list, description="Previous actions taken")

class NavigatorResponse(BaseModel):
    """Response from the /plan endpoint"""
    action: ActionType = Field(..., description="Next action to perform")
    elementId: Optional[int] = Field(None, description="ID of target element")
    text: Optional[str] = Field(None, description="Text to type (for TYPE actions)")
    summary: Optional[str] = Field(None, description="Summary of completion (for DONE actions)")
    reasoning: Optional[str] = Field(None, description="AI's reasoning for this action")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Environment name")
    ai_model: str = Field(..., description="AI model being used")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

# Website context models for RAG
class WebsiteContext(BaseModel):
    """Website understanding context"""
    page_type: str = Field(..., description="Type of page (home, products, cart, etc.)")
    available_actions: List[str] = Field(..., description="Actions available on this page")
    common_patterns: Dict[str, str] = Field(..., description="Common UI patterns on this site")
    navigation_structure: Dict[str, Any] = Field(..., description="Site navigation structure")

class IntentAnalysis(BaseModel):
    """User intent analysis result"""
    primary_intent: str = Field(..., description="Primary user intent")
    entities: List[str] = Field(..., description="Extracted entities from query")
    required_steps: List[str] = Field(..., description="Steps needed to fulfill intent")
    confidence: float = Field(..., description="Confidence in intent analysis")

class ActionPlan(BaseModel):
    """Action planning result"""
    current_step: int = Field(..., description="Current step number")
    total_steps: int = Field(..., description="Total estimated steps")
    next_action: Action = Field(..., description="Next action to take")
    reasoning: str = Field(..., description="Reasoning for this action")
    alternative_actions: List[Action] = Field(default_factory=list, description="Alternative actions considered")

# LLM Response Schemas for strict validation
class LLMNextAction(BaseModel):
    """Schema for next_action in LLM responses"""
    action: ActionType = Field(..., description="Type of action to perform")
    elementId: Optional[int] = Field(None, description="ID of target element")
    text: Optional[str] = Field(None, description="Text to type (for TYPE actions)")
    summary: Optional[str] = Field(None, description="Summary of completion (for DONE actions)")

class LLMActionPlanSchema(BaseModel):
    """Strict schema for LLM action planning responses"""
    current_step: int = Field(..., ge=1, description="Current step number (must be >= 1)")
    total_steps: int = Field(..., ge=1, description="Total estimated steps (must be >= 1)")
    next_action: LLMNextAction = Field(..., description="Next action to take")
    reasoning: str = Field(..., min_length=1, description="Reasoning for this action (cannot be empty)")
    alternative_actions: List[LLMNextAction] = Field(default_factory=list, description="Alternative actions considered")

class LLMIntentAnalysisSchema(BaseModel):
    """Strict schema for LLM intent analysis responses"""
    primary_intent: str = Field(..., min_length=1, description="Primary user intent (cannot be empty)")
    entities: List[str] = Field(default_factory=list, description="Extracted entities from query")
    required_steps: List[str] = Field(..., min_items=1, description="Steps needed (at least one step required)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
