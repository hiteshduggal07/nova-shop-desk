"""
AI Decision Engine using GPT-4o-mini for website navigation
"""

import json
import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from models import (
    DOMElement, Action, ActionType, NavigatorRequest, NavigatorResponse,
    IntentAnalysis, ActionPlan, WebsiteContext,
    LLMIntentAnalysisSchema, LLMActionPlanSchema
)
from config import settings
from json_validation import initialize_validator, validate_llm_response, JSONValidationError

logger = logging.getLogger(__name__)

class AIDecisionEngine:
    """AI engine that decides what actions to take based on user queries and DOM state"""
    
    def __init__(self):
        # Log API key status for debugging (without exposing the key)
        api_key = settings.openai_api_key
        logger.info(f"Initializing OpenAI client with key length: {len(api_key) if api_key else 0}")
        logger.info(f"Using model: {settings.openai_model}")
        
        if not api_key or len(api_key) < 10:
            logger.warning("OpenAI API key appears to be missing or too short")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = settings.openai_model
        
        # Initialize JSON validation system
        initialize_validator(self.client, self.model, max_retries=3)
        logger.info("✓ JSON validation system initialized")
        
    async def analyze_intent(self, query: str, history: List[Action]) -> IntentAnalysis:
        """Analyze user intent from the query"""
        
        system_prompt = """You are an expert at analyzing user intent for e-commerce website navigation.
        
        Your task is to understand what the user wants to accomplish and break it down into actionable steps.
        
        Common e-commerce intents include:
        - SEARCH: Finding products (e.g., "search for leather wallet")
        - ADD_TO_CART: Adding items to shopping cart
        - CHECKOUT: Proceeding to checkout
        - NAVIGATE: Moving to different pages
        - VIEW_PRODUCT: Looking at product details
        - FILTER: Applying filters to product listings
        - REMOVE_FROM_CART: Removing items from cart
        
        You MUST respond with ONLY a valid JSON object in this exact format:
        {
            "primary_intent": "NAVIGATE",
            "entities": [],
            "required_steps": ["step1", "step2"],
            "confidence": 0.8
        }
        
        Do not include any explanation or markdown formatting. Only return the JSON object.
        """
        
        user_message = f"""
        User Query: "{query}"
        
        Previous Actions: {[action.model_dump() for action in history]}
        
        Analyze the user's intent and provide the required JSON response.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=settings.temperature,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            logger.debug(f"Raw OpenAI response for intent analysis: {content}")
            
            # Use strict JSON validation with automatic retry
            validated_result = await validate_llm_response(
                content=content,
                schema_class=LLMIntentAnalysisSchema,
                messages=messages,
                operation_name="Intent Analysis"
            )
            
            # Convert to the expected IntentAnalysis model
            return IntentAnalysis(
                primary_intent=validated_result.primary_intent,
                entities=validated_result.entities,
                required_steps=validated_result.required_steps,
                confidence=validated_result.confidence
            )
            
        except JSONValidationError as e:
            logger.error(f"JSON validation failed for intent analysis after all retries: {e}")
            # Fallback intent analysis
            return IntentAnalysis(
                primary_intent="NAVIGATE",
                entities=[],
                required_steps=["Navigate to complete the user's request"],
                confidence=0.5
            )
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            # Fallback intent analysis
            return IntentAnalysis(
                primary_intent="NAVIGATE",
                entities=[],
                required_steps=["Navigate to complete the user's request"],
                confidence=0.5
            )
    
    async def plan_next_action(
        self, 
        request: NavigatorRequest,
        intent: IntentAnalysis,
        website_context: Optional[WebsiteContext] = None
    ) -> ActionPlan:
        """Plan the next action based on current state and intent"""
        
        system_prompt = """You are an expert web automation agent for an e-commerce website.
        
        Your job is to decide the next action to take based on:
        1. User's intent and query
        2. Current DOM elements available
        3. Action history (what has been done so far)
        4. Website context and patterns
        
        AVAILABLE ACTIONS:
        - CLICK: Click on buttons, links, or interactive elements
        - TYPE: Type text into input fields
        - DONE: Mark the task as completed
        
        DECISION RULES:
        1. Always choose the most logical next step toward fulfilling the user's intent
        2. If you need to search, first click on search input, then type search term
        3. If you need to add to cart, find and click "Add to Cart" button
        4. If you need to checkout, navigate to cart then checkout
        5. If you can't find the right element, mark as DONE with explanation
        6. Be specific about which element to interact with based on ID
        
        You MUST respond with ONLY a valid JSON object in this exact format:
        {
            "current_step": 1,
            "total_steps": 2,
            "next_action": {"action": "CLICK", "elementId": 5, "text": null, "summary": null},
            "reasoning": "explanation of why this action was chosen",
            "alternative_actions": []
        }
        
        Do not include any explanation or markdown formatting. Only return the JSON object.
        """
        
        # Prepare DOM elements description
        dom_description = []
        for element in request.dom_snapshot:
            desc = f"ID {element.id}: {element.tag}"
            if element.text:
                desc += f" with text '{element.text[:50]}'"
            if element.type:
                desc += f" (type: {element.type})"
            if element.placeholder:
                desc += f" (placeholder: '{element.placeholder}')"
            dom_description.append(desc)
        
        user_message = f"""
        USER QUERY: "{request.query}"
        USER INTENT: {intent.primary_intent}
        ENTITIES: {intent.entities}
        REQUIRED STEPS: {intent.required_steps}
        
        CURRENT DOM ELEMENTS:
        {chr(10).join(dom_description)}
        
        ACTION HISTORY:
        {[f"Step {i+1}: {action.action}" + (f" on element {action.elementId}" if action.elementId else "") + (f" with text '{action.text}'" if action.text else "") for i, action in enumerate(request.history)]}
        
        WEBSITE CONTEXT:
        {website_context.model_dump() if website_context else "No specific context available"}
        
        IMPORTANT: For this specific query "{request.query}":
        - If looking for checkout and there's no obvious checkout button, look for cart-related links first
        - Check element IDs 4-6 which might be cart/user icons
        - Consider that checkout usually requires items in cart first
        - If you have already performed {len(request.history)} actions, strongly consider if the task is complete
        - If you've successfully clicked relevant elements or completed the main intent, return DONE
        - NEVER repeat the same action on the same element multiple times
        
        COMPLETION CRITERIA:
        - For "search" queries: 
          1. First click on search input field
          2. Then type the search term
          3. Then click search button or press Enter (the form will handle submission)
          4. Task is DONE after these steps
        - For "go to X page" queries: After clicking the relevant navigation link, task is DONE
        - For "add to cart" queries: After clicking "Add to Cart" button, task is DONE
        - If you can't find the exact element after 3-4 attempts, task is DONE with explanation
        
        SEARCH WORKFLOW SPECIFIC INSTRUCTIONS:
        - Look for input elements with type="text" or placeholder containing "search"
        - After typing in search field, look for button with "Search" text or search icon
        - The search functionality is in the navigation bar, look for elements early in the DOM list
        
        What should be the next action? Provide your response as JSON.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=settings.temperature,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            logger.debug(f"Raw OpenAI response for action planning: {content}")
            
            # Use strict JSON validation with automatic retry
            validated_result = await validate_llm_response(
                content=content,
                schema_class=LLMActionPlanSchema,
                messages=messages,
                operation_name="Action Planning"
            )
            
            # Convert the validated result to ActionPlan model
            next_action = Action(
                action=validated_result.next_action.action,
                elementId=validated_result.next_action.elementId,
                text=validated_result.next_action.text,
                summary=validated_result.next_action.summary
            )
            
            alternative_actions = [
                Action(
                    action=alt.action,
                    elementId=alt.elementId,
                    text=alt.text,
                    summary=alt.summary
                ) for alt in validated_result.alternative_actions
            ]
            
            return ActionPlan(
                current_step=validated_result.current_step,
                total_steps=validated_result.total_steps,
                next_action=next_action,
                reasoning=validated_result.reasoning,
                alternative_actions=alternative_actions
            )
            
        except JSONValidationError as e:
            logger.error(f"JSON validation failed for action planning after all retries: {e}")
            # Fallback action plan
            return ActionPlan(
                current_step=len(request.history) + 1,
                total_steps=len(request.history) + 1,
                next_action=Action(
                    action=ActionType.DONE,
                    summary="Unable to determine next action due to JSON validation error"
                ),
                reasoning="Fallback due to JSON validation failure",
                alternative_actions=[]
            )
        except Exception as e:
            logger.error(f"Error planning next action: {e}")
            # Fallback action plan
            return ActionPlan(
                current_step=len(request.history) + 1,
                total_steps=len(request.history) + 1,
                next_action=Action(
                    action=ActionType.DONE,
                    summary="Unable to determine next action due to AI processing error"
                ),
                reasoning="Fallback due to AI engine error",
                alternative_actions=[]
            )
    
    async def decide_action(self, request: NavigatorRequest) -> NavigatorResponse:
        """Main decision method that combines intent analysis and action planning"""
        
        logger.info(f"Processing query: {request.query}")
        logger.info(f"DOM elements: {len(request.dom_snapshot)}")
        logger.info(f"History length: {len(request.history)}")
        
        # Check for infinite loop - if we have too many actions, force completion
        if len(request.history) >= 6:
            logger.warning(f"Too many actions ({len(request.history)}), forcing completion")
            return NavigatorResponse(
                action=ActionType.DONE,
                summary=f"Task completed after {len(request.history)} steps. The command '{request.query}' has been processed.",
                reasoning="Completed due to step limit to prevent infinite loops",
                confidence=0.7
            )
        
        # Check for repeated identical actions (potential infinite loop)
        if len(request.history) >= 2:
            recent_actions = request.history[-2:]
            if all(action.action == recent_actions[0].action and 
                   action.elementId == recent_actions[0].elementId for action in recent_actions):
                logger.warning("Detected repeated identical actions, forcing completion")
                return NavigatorResponse(
                    action=ActionType.DONE,
                    summary=f"Task completed. Detected repeated actions, stopping to prevent loops.",
                    reasoning="Stopped due to repeated identical actions",
                    confidence=0.6
                )
        
        # Check if we've completed common task patterns
        if len(request.history) >= 2:
            last_action = request.history[-1]
            
            # For search queries, check if we've completed the search flow
            if "search" in request.query.lower():
                type_actions = [a for a in request.history if a.action == "TYPE"]
                click_actions = [a for a in request.history if a.action == "CLICK"]
                
                # If we've typed something and clicked (likely the search button), we're done
                if len(type_actions) >= 1 and len(click_actions) >= 2:
                    logger.info("Search workflow appears complete (typed + clicked search), forcing DONE")
                    return NavigatorResponse(
                        action=ActionType.DONE,
                        summary=f"Search for '{type_actions[-1].text}' completed successfully.",
                        reasoning="Search workflow completed: typed search term and clicked search button",
                        confidence=0.9
                    )
        
        try:
            # Step 1: Analyze user intent
            intent = await self.analyze_intent(request.query, request.history)
            logger.info(f"Analyzed intent: {intent.primary_intent}")
            
            # Step 2: Get website context (this could be enhanced with RAG)
            website_context = await self.get_website_context(request.dom_snapshot)
            
            # Step 3: Plan next action
            action_plan = await self.plan_next_action(request, intent, website_context)
            logger.info(f"Planned action: {action_plan.next_action.action}")
            
            # Step 4: Create response
            response = NavigatorResponse(
                action=action_plan.next_action.action,
                elementId=action_plan.next_action.elementId,
                text=action_plan.next_action.text,
                summary=action_plan.next_action.summary,
                reasoning=action_plan.reasoning,
                confidence=intent.confidence
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in AI decision engine: {e}")
            return NavigatorResponse(
                action=ActionType.DONE,
                summary=f"Error processing request: {str(e)}",
                reasoning="AI engine encountered an error",
                confidence=0.0
            )
    
    async def get_website_context(self, dom_elements: List[DOMElement]) -> WebsiteContext:
        """Analyze DOM to understand website context"""
        
        # Simple heuristic-based context detection
        # This could be enhanced with RAG for better understanding
        
        page_type = "unknown"
        available_actions = []
        common_patterns = {}
        
        # Detect page type based on DOM elements
        element_texts = [elem.text.lower() for elem in dom_elements if elem.text]
        
        if any("search" in text for text in element_texts):
            available_actions.append("search")
            common_patterns["search"] = "Search functionality available"
        
        if any("cart" in text or "add to cart" in text for text in element_texts):
            available_actions.append("add_to_cart")
            common_patterns["cart"] = "Shopping cart functionality available"
        
        if any("checkout" in text for text in element_texts):
            available_actions.append("checkout")
            page_type = "cart"
        
        if any("product" in text or "price" in text for text in element_texts):
            page_type = "products"
            available_actions.append("view_product")
        
        if any("home" in text for text in element_texts):
            page_type = "home"
        
        return WebsiteContext(
            page_type=page_type,
            available_actions=available_actions,
            common_patterns=common_patterns,
            navigation_structure={"detected": "basic"}
        )
